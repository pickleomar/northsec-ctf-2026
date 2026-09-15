/* masjid_os_hard.c
 *
 * Masjid OS - Hardened Edition
 * Features: Anti-debugging and runtime key generation.
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include "banner.h"
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#include <sys/ptrace.h> /* REQUIRED for anti-debug */
#include <unistd.h>

/* --- SPIRITUAL FIREWALL (Anti-Debug) --- */
void spiritual_firewall() {
    // PTRACE_TRACEME checks if a debugger is already attached.
    // If gdb is running this, it returns -1.
    if (ptrace(PTRACE_TRACEME, 0, 1, 0) < 0) {
        puts("(!) ASTAGHFIRULLAH: Debugger detected.");
        puts("    You cannot peek into the soul of the machine directly.");
        exit(1);
    }
}

/* --- KEY GENERATION (Runtime Obfuscation) --- */
/* The key is NOT stored statically. It is generated here. */
static uint64_t vm_key = 0; 

void perform_ablution() {
    // Generates 0xfeedc0de12345678 at runtime.
    // Static analysis will only see '0' in the data section.
    uint64_t part_a = 0xfeedc0de00000000;
    uint64_t part_b = 0x0000000012345678;
    vm_key = part_a | part_b; 
}

/* --- CONSTANTS & STRINGS --- */
static const char *GREETING = "marhba bik akhi fi lmasjid\n\n";
static const char *FINAL_MESSAGE = "i always outsmart you with one step akhi\n";

static const char *HELP_TEXT =
"masjid os help\n\n"
"available commands:\n"
"ls        list paths\n"
"cd        change path\n"
"pwd       show current path\n"
"cat       read scripture\n"
"whoami    show identity\n"
"clear     cleanse screen\n"
"exit      leave the system\n\n"
"spiritual commands:\n"
"zikr\n"
"salat\n"
"siyam\n"
"zakat\n"
"haj\n"
"dua\n"
"niyah\n";

/* Encrypted flag: "nsc{m@@ch44lah_4kh11_y0u_4r3_$mart3r_th3n_d3m0n$}" XOR 0xfeedc0de12345678 */
/* Note: Since the key is runtime generated, this blob looks like garbage until runtime. */
static const unsigned char encrypted_flag[] = {
    0x16,0x25,0x57,0x69,0xb3,0x80,0xad,0x9d,0x10,0x62,0x00,0x7e,0xbf,0xa8,0xb2,0xca,
    0x13,0x3e,0x05,0x23,0x81,0xb9,0xdd,0x8b,0x27,0x62,0x46,0x21,0x81,0xe4,0x80,0x9f,
    0x0a,0x22,0x07,0x60,0x81,0xb4,0x85,0xcd,0x16,0x09,0x50,0x21,0xb3,0xf0,0x83,0xda,
    0x05
};
static char decrypted_flag[128];
static int unlocked = 0;

/* --- STATE VARIABLES --- */
static uint32_t command_counter = 0;
static uint64_t ramadan_acc_num = 0;
static uint64_t mobarak_acc_num = 0;
static char ramadan_acc[8] = {0};
static char mobarak_acc[8] = {0};
static int personality = 0;
static int hijack_flag = 0;

/* --- LOGIC HELPERS --- */
static inline uint64_t rol64(uint64_t x, unsigned n) {
    return (x << n) | (x >> (64 - n));
}

static uint64_t cmd_hash_calc(const char *s) {
    uint64_t h = 0;
    for (; *s; ++s) {
        unsigned char c = (unsigned char)*s;
        h = h * 17 + c;
    }
    return h;
}

static uint64_t arg_hash_calc(const char *s) {
    uint64_t h = 0;
    for (; *s; ++s) {
        unsigned char c = (unsigned char)*s;
        h = (h * 31) ^ c;
    }
    return h;
}

static void normalize_inplace(char *s) {
    while (*s && isspace((unsigned char)*s)) memmove(s, s+1, strlen(s));
    size_t len = strlen(s);
    while (len && isspace((unsigned char)s[len-1])) s[--len] = '\0';
    for (size_t i = 0; i < len; ++i) s[i] = (char)tolower((unsigned char)s[i]);
}

/* --- GAME LOGIC --- */
static const char RAMADAN_TABLE[7] = {'r','a','m','a','d','a','n'};
static const char MOBARAK_TABLE[7] = {'m','o','b','a','r','a','k'};
static int last_letter_index = -1;

static void corrupt_state(void) {
    ramadan_acc_num ^= 0xdeadbeefcafebabeULL;
    mobarak_acc_num ^= 0xabad1dea0badf00dULL;
    for (int i = 0; i < 7; ++i) {
        ramadan_acc[i] = (char)(ramadan_acc[i] ^ 0x5A);
        mobarak_acc[i]  = (char)(mobarak_acc[i]  ^ 0xA5);
    }
}

static void attempt_append_ramadan(int idx) {
    if (command_counter < 1 || command_counter > 14) { corrupt_state(); return; }
    if (last_letter_index == idx) {
        for (int i = 0; i < 7; ++i) if (ramadan_acc[i] == 0) { ramadan_acc[i] = RAMADAN_TABLE[idx]; ramadan_acc_num = (ramadan_acc_num << 8) | (uint64_t)RAMADAN_TABLE[idx]; break; }
    } else {
        last_letter_index = idx;
    }
}

static void attempt_append_mobarak(int idx) {
    if (command_counter < 15 || command_counter > 28) { corrupt_state(); return; }
    if (last_letter_index == idx) {
        for (int i = 0; i < 7; ++i) if (mobarak_acc[i] == 0) { mobarak_acc[i] = MOBARAK_TABLE[idx]; mobarak_acc_num = (mobarak_acc_num << 8) | (uint64_t)MOBARAK_TABLE[idx]; break; }
    } else {
        last_letter_index = idx;
    }
}

/* --- COMMAND HANDLERS --- */
static void handle_help(void) { puts(HELP_TEXT); }
static void handle_ls(void) { puts("."); puts(".. "); puts("readme"); puts("flag.txt"); }
static void handle_pwd(void) { puts("/home/masjid"); }
static void handle_cd(const char *arg) { (void)arg; puts("changed path"); }
static void handle_cat(const char *arg) { if (arg && strcmp(arg, "flag.txt") == 0) puts("NSC{RAK_NADI_AKHI_MOU2MINE}"); else if (arg && strcmp(arg, "readme") == 0) puts("welcome to masjid os - nothing to see here"); else puts("cat: nothing to read"); }
static void handle_whoami(void) { puts("AITSSI"); }
static void handle_clear(void) { for (int i = 0; i < 50; ++i) putchar('\n'); }

static void handle_zikr(uint64_t input_number) { puts("subhanallah"); int idx = (int)(input_number % 7); idx = (idx + personality) % 7; if (command_counter >=1 && command_counter <=14) attempt_append_ramadan(idx); else if (command_counter >=15 && command_counter <=28) attempt_append_mobarak(idx); }
static void handle_salat(uint64_t input_number) { (void)input_number; puts("prayer accepted"); last_letter_index = -1; }
static void handle_siyam(void) { puts("patience..."); command_counter += 1; }
static void handle_zakat(void) { puts("purification complete"); if (command_counter <= 28) { if (ramadan_acc[0]) ramadan_acc[0] ^= 0xFF; if (mobarak_acc[0]) mobarak_acc[0] ^= 0xFF; } }
static void handle_haj(void) { puts("journey recorded"); hijack_flag = 1; }
static void handle_dua(uint64_t arg_hash) { puts("amen"); if (arg_hash) vm_key ^= arg_hash; }
static void handle_niyah(uint64_t arg_hash) { puts("intention noted"); personality = (int)(arg_hash % 7); }

static void check_win_and_decrypt(void) {
    if (command_counter == 40) {
        if (strcmp(ramadan_acc, "ramadan") == 0 && strcmp(mobarak_acc, "mobarak") == 0) {
            size_t len = sizeof(encrypted_flag)/sizeof(encrypted_flag[0]);
            for (size_t i = 0; i < len; ++i) decrypted_flag[i] = (char)(encrypted_flag[i] ^ ((char)((vm_key >> ((i%8)*8)) & 0xFF)));
            decrypted_flag[len] = '\0';
            unlocked = 1;
            if (getenv("MASJID_DEBUG") && strcmp(getenv("MASJID_DEBUG"), "1") == 0) printf("DEBUG FLAG: %s\n", decrypted_flag);
            if (unlocked) puts(FINAL_MESSAGE);
        }
    }
}

/* --- MAIN --- */
int main(void) {
    // 1. Activate Firewall (Stops Debuggers)
    spiritual_firewall();
    
    // 2. Generate Key (Calculates key at runtime)
    perform_ablution();

    puts(banner);
    fputs(GREETING, stdout);
    
    char *line = NULL;
    size_t sz = 0;
    
    while (1) {
        fputs("masjid_os> ", stdout);
        fflush(stdout);
        
        ssize_t r = getline(&line, &sz, stdin);
        
        // --- FIX FOR WARNING ---
        if (r <= 0) break;
        if (line[r-1] == '\n') line[r-1] = '\0';
        // -----------------------

        normalize_inplace(line);
        if (line[0] == '\0') continue;
        
        char *space = strchr(line, ' ');
        char cmdbuf[256] = {0};
        char argbuf[768] = {0};
        
        if (space) {
            size_t clen = (size_t)(space - line);
            if (clen >= sizeof(cmdbuf)) clen = sizeof(cmdbuf)-1;
            memcpy(cmdbuf, line, clen);
            strncpy(argbuf, space+1, sizeof(argbuf)-1);
            normalize_inplace(argbuf);
        } else {
            strncpy(cmdbuf, line, sizeof(cmdbuf)-1);
        }
        
        uint64_t cmdh = cmd_hash_calc(cmdbuf);
        uint64_t argh = arg_hash_calc(argbuf);
        uint64_t input_number = cmdh ^ rol64(argh, 3) ^ (uint64_t)command_counter;
        
        command_counter++;
        
        if (cmdh == cmd_hash_calc("help")) handle_help();
        else if (cmdh == cmd_hash_calc("ls")) handle_ls();
        else if (cmdh == cmd_hash_calc("pwd")) handle_pwd();
        else if (cmdh == cmd_hash_calc("cd")) handle_cd(argbuf);
        else if (cmdh == cmd_hash_calc("cat")) handle_cat(argbuf);
        else if (cmdh == cmd_hash_calc("whoami")) handle_whoami();
        else if (cmdh == cmd_hash_calc("clear")) handle_clear();
        else if (cmdh == cmd_hash_calc("exit")) { puts(FINAL_MESSAGE); break; }
        else if (cmdh == cmd_hash_calc("zikr")) handle_zikr(input_number);
        else if (cmdh == cmd_hash_calc("salat")) handle_salat(input_number);
        else if (cmdh == cmd_hash_calc("siyam")) handle_siyam();
        else if (cmdh == cmd_hash_calc("zakat")) handle_zakat();
        else if (cmdh == cmd_hash_calc("haj")) handle_haj();
        else if (cmdh == cmd_hash_calc("dua")) handle_dua(argh);
        else if (cmdh == cmd_hash_calc("niyah")) handle_niyah(argh);
        else { printf("%s: command not found\n", cmdbuf); corrupt_state(); }
        
        int letter_index = (int)(input_number % 7);
        letter_index = (letter_index + personality) % 7;
        
        if (command_counter >= 29 && command_counter <= 40) {
            if (!(cmdh == cmd_hash_calc("zikr") || cmdh == cmd_hash_calc("salat"))) corrupt_state();
        }
        
        check_win_and_decrypt();
    }
    
    free(line);
    return 0;
}
