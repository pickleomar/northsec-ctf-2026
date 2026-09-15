#include "ksh.h"

// Whitelisted commands that the shell allows to execute
const char* whitelist[] = { "cd", "history", "delete", "help", "ls", "cat", "echo", "!", "id", "whoami", "clear", "cwd", "pwd" };

// Command table mapping command names to their corresponding functions
Command commands[] = {
    { "history", view_history },
    { "delete", delete_command },
    { "clear", clear_terminal },
    { "help", view_help },
    { "cwd", view_cwd },
    { "cd", change_directory },
    { "!!", exec_history },
    { "!", exec_history }
};

// Parses the input into a command and arguments
int parse_args(const char* input, char* command, char** argv)
{
    strncpy(command, input, MAX_INPUT_SIZE - 1);
    command[MAX_INPUT_SIZE - 1] = '\0';

    int argc = 0;
    char* token = strtok(command, " ");
    while (token && argc < MAX_ARGS - 1) {
        argv[argc++] = token;
        token = strtok(NULL, " ");
    }
    argv[argc] = NULL;
    return argc;
}

// Checks if the input command is allowed (whitelisted)
int check_command(char* input)
{
    char command[MAX_INPUT_SIZE] = { 0 };
    char* argv[MAX_ARGS] = { 0 };
    int argc = parse_args(input, command, argv);

    // no arguments
    if (argc <= 0) {
        return -1;
    }

    int allowed = 0;

    // Check if the command is in the whitelist
    for (int i = 0; i < (int)(sizeof(whitelist) / sizeof(whitelist[0])); i++) {
        if (!strncmp(argv[0], whitelist[i], strlen(whitelist[i]))) {
            allowed = 1;
            break;
        }
    }

    if (!allowed) {
        return -1;
    }

    if (argc > 1) {
        int c = 0;
        while (argv[c] && c != argc) {
            // follow symlinks to cat's argument
            char real_path[PATH_MAX] = { 0 };
            if (realpath(argv[c++], real_path) && strstr(real_path, "flag") != NULL) {
                return -1;
            }
        }
    }

    // If command passes both checks, return 0
    return 0;
}

// Runs an external command using fork-exec
int run_cmd(char* input)
{

    char command[MAX_INPUT_SIZE] = { 0 };
    char* argv[MAX_ARGS] = { 0 };
    int argc = parse_args(input, command, argv);

    if (argc > 0) {
        pid_t pid = fork();
        if (pid == -1) {
            perror("fork failed");
            return -1;
        } else if (pid == 0) {
            execvp(argv[0], argv);
            perror("execvp failed");
            exit(EXIT_FAILURE);
        } else {
            int status;
            waitpid(pid, &status, 0);
            if (WIFEXITED(status)) {
                return WEXITSTATUS(status);
            }
        }
    }
    return -1;
}

// Executes a built-in command or falls back to an external command
int execute_command(CommandHistory* history, char* input)
{
    for (int i = 0; i < (int)(sizeof(commands) / sizeof(commands[0])); i++) {
        if (strncmp(input, commands[i].name, strlen(commands[i].name)) == 0) {
            return commands[i].function(history, input);
        }
    }

    return run_cmd(input);
}

// Adds a command to the history (ignores history execution commands)
void add_command(CommandHistory* history, char* command)
{
    if (history->count == MAX_HISTORY) {
        printf("History is full. Cannot add new command.\n");
        return;
    }
    if (!strncmp(command, "!", 1)) {
        return;
    }
    history->commands[history->count] = command;
    history->count++;
}

// TODO: clear the free'd pointer, apparently it's causing crashes in release version
// Deletes a command from history by index
int delete_command(CommandHistory* history, const char* input)
{
    int index = atoi(input + 7);
    if (index < 0 || index >= history->count) {
        printf("Invalid index.\n");
        return -1;
    }
    free(history->commands[index]);
    return 0;
}

// Displays command history
int view_history(CommandHistory* history, const char* input)
{
    (void)input;
    for (int i = 0; i < history->count; i++) {
        if (history->commands[i] != NULL) {
            printf("%d: %s\n", i, history->commands[i]);
        }
    }
    return 0;
}

// Prints the shell prompt with user and machine info
void print_prompt()
{
    // Get user and machine info for the prompt
    struct passwd* pw = getpwuid(getuid());
    if (!pw) {
        printf("\033[1;32m$ \033[0m");
        return;
    }
    char* user = pw->pw_name;
    char* machine = "northsec-ctf";

    // Get the current directory relative to home
    char* home_dir = getenv("HOME");
    if (!home_dir) {
        printf("\033[1;32m%s@%s\033[0m:\033[1;34m$ \033[0m", user, machine);
        return;
    }

    char cwd[PATH_MAX];
    if (getcwd(cwd, sizeof(cwd)) == NULL) {
        printf("\033[1;32m%s@%s\033[0m:\033[1;34m$ \033[0m", user, machine);
        return;
    }

    // Display relative path if inside home directory
    if (strncmp(cwd, home_dir, strlen(cwd)) == 0) {
        printf("\033[1;32m%s@%s\033[0m:\033[1;34m~%s\033[0m$ ", user, machine, cwd + strlen(home_dir));
    } else {
        printf("\033[1;32m%s@%s\033[0m:\033[1;34m%s\033[0m$ ", user, machine, cwd);
    }
}

// Reads user input and returns it as a dynamically allocated string
char* read_input()
{
    char buffer[MAX_INPUT_SIZE];
    int index = 0;
    char c;
    ssize_t bytes_read;

    while (index < MAX_INPUT_SIZE - 1) {
        bytes_read = read(0, &c, 1);
        if (bytes_read <= 0 || c == 4 || c == 3) { // Handle EOF (Ctrl-D) and Interrupt (Ctrl-C)
            return NULL;
        }
        if (c == '\n') {
            break;
        }
        buffer[index++] = c;
    }
    buffer[index] = '\0';

    // store the user input on the heap using malloc
    char* input = (char*)malloc(index + 1);
    if (!input) {
        printf("Memory allocation failed.\n");
        return NULL;
    }
    strcpy(input, buffer);
    return input;
}

// Changes the working directory
int change_directory(CommandHistory* history, const char* input)
{
    (void)history;
    char* path = (char*)input + 3; // Skip "cd "
    if (chdir(path) != 0) {
        printf("ksh: no such file or directory\n");
        return -1;
    }
    return 0;
}

// Clears the terminal screen
int clear_terminal(CommandHistory* history, const char* input)
{
    (void)history;
    (void)input;
    printf("\033[H\033[J");
    return 0;
}

// Prints the current working directory
int view_cwd(CommandHistory* history, const char* input)
{
    (void)history;
    (void)input;
    char cwd[0x100] = { 0 };
    if (!getcwd(cwd, sizeof(cwd))) {
        return -1;
    }
    printf("%s\n", cwd);
    return 0;
}

// Executes commands from history (! or !!)
// Do not call check_command again on history entries
// because commands in history are already trusted commands
int exec_history(CommandHistory* history, const char* input)
{
    if (strcmp(input, "!!") == 0) {
        if (history->count == 0) {
            printf("No commands in history.\n");
            return -1;
        }
        printf("%s\n", history->commands[history->count - 1]);
        // i think its fine to just execute without checking, this will save 0.4ms
        return execute_command(history, history->commands[history->count - 1]);
    } else if (input[0] == '!' && isdigit(input[1])) {
        int index = atoi(&input[1]);
        if (index >= 0 && index < history->count && history->commands[index] != NULL) {
            printf("%s\n", history->commands[index]);
            // i think its fine to just execute without checking, this will save 0.4ms
            return execute_command(history, history->commands[index]);
        } else {
            printf("Invalid history index.\n");
        }
    } else {
        printf("Invalid history command format. Use !! or !<index>.\n");
    }
    return 0;
}

// Displays help information
int view_help(CommandHistory* history, const char* input)
{
    (void)history;
    (void)input;
    printf("List of `ksh` built-in commands:\n");
    printf("cd <dir>           - Change directory\n");
    printf("clear              - Clear screen\n");
    printf("cwd                - Current working directory\n");
    printf("history            - View command history\n");
    printf("delete <index>     - Delete command from history\n");
    printf("!<index>           - Execute command from history\n");
    printf("!!                 - Execute the most recent command from history\n");
    printf("help               - Show this help message\n");
    return 0;
}

int main()
{
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);

    CommandHistory history = { .count = 0 };
    char* input = NULL;
    int res = 0;

    printf("\nksh v1.1 (release build @bld_mhd)\n");
    printf("check `help` for a list of builtin commands.\n\n");
    while (1) {
        print_prompt();
        input = read_input();
        if (!input) {
            break;
        }

        if (check_command(input) < 0) {
            continue;
        }

        // Execute the command using the new function
        res = execute_command(&history, input);
        add_command(&history, input);
    }

    return res;
}
