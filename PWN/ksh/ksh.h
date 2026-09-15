#ifndef XSH_H
#define XSH_H

#include <pwd.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <limits.h>
#include <sys/wait.h>
#include <sys/types.h>

#define MAX_ARGS 10
#define MAX_HISTORY 64
#define MAX_COMMAND_LENGTH 256
#define MAX_INPUT_SIZE 1024

typedef struct {
    char* commands[MAX_HISTORY];
    int count;
} CommandHistory;

typedef struct {
    const char* name;
    int (*function)(CommandHistory* history, const char* input);
} Command;

void add_command(CommandHistory* history, char* command);
int delete_command(CommandHistory* history, const char* input);
int view_history(CommandHistory* history, const char* input);
int change_directory(CommandHistory* history, const char* input);
int clear_terminal(CommandHistory* history, const char* input);
int view_cwd(CommandHistory* history, const char* input);
int exec_history(CommandHistory* history, const char* input);
int view_help(CommandHistory* history, const char* input);
int parse_args(const char* input, char* command, char** argv);
int execute_command(CommandHistory* history, char* input);
int check_command(char* input);
int run_cmd(char* input);
void print_prompt();
char* read_input();

#endif // XSH_H
