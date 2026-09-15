/* main.c
 *
 * AITSSI-OS - Fitna Edition (9.5/10)
 * Architecture: x86_64 Linux
 * Compile: gcc -O0 -fno-stack-protector main.c -o masjid_rahma
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <signal.h>
#include <ucontext.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include "banner.h"

/* --- 1. ABYSS DATA --- */
static const unsigned char encrypted_flag[] = {
    0x41, 0xc2, 0x3c, 0x95, 0x54, 0x60, 0xa3, 0x89, 0x50, 0xf7, 0x4c, 0x85, 
    0x4b, 0x36, 0x80, 0x93, 0x64, 0xce, 0x4b, 0x85, 0x4b, 0x65, 0xf1, 0xbe, 
    0x62, 0xa1, 0xa, 0xdc, 0x4e, 0x65, 0xae, 0x9c
};

/* --- 2. ABYSS STATE --- */
static uint64_t unseen_table[256];
static uint64_t real_state = 0;
static uint64_t shadow_state = 0;
static uint64_t path_entropy = 0xc0deba5eULL;
static int step_index = 0;
static int abyss_mode = 0;

/* --- 3. THE ABLUTION (Environment Seeding & Mirror Trap) --- */
void perform_ablution() {
    // FITNA UPGRADE 2: Subtle ptrace check (Mirror Trap)
    // If traced, the seed changes slightly. Result: Same behavior, wrong states.
    uint64_t trap_seed = 0;
    if (ptrace(PTRACE_TRACEME, 0, 1, 0) < 0) {
        trap_seed = 0xBAD1337BEEF00000ULL;
    }

    uint64_t seed = 0xfeedc0de1337beefULL ^ trap_seed;
    for(int i = 0; i < 256; i++) {
        seed ^= (seed << 13);
        seed ^= (seed >> 7);
        seed ^= (seed << 17);
        unseen_table[i] = seed;
    }
    
    // FITNA UPGRADE 1: Environment-Coupled Seeding
    // This makes static simulation impossible without knowing the target env.
    // For this CTF, we fix the "righteous" env state but use PID to mix if needed.
    real_state = unseen_table[0];
    shadow_state = 0xdeadbeef12345678ULL;
}

/* --- 4. THE ABYSS HANDLER (Branching VM) --- */
void abyss_handler(int sig, siginfo_t *info, void *context) {
    ucontext_t *uc = (ucontext_t *)context;

    if (sig == SIGILL) {
        // Anti-Analysis
        uc->uc_mcontext.gregs[REG_RAX] ^= 0xbadc0ded;

        uint64_t base_op = uc->uc_mcontext.gregs[REG_R8];
        step_index++;

        if (abyss_mode) {
            // Abyss Mode: Divergent states
            real_state ^= 0x666;
            shadow_state ^= 0x999;
        } else {
            // FITNA UPGRADE 3: State-Dependent Command Lexing
            // After 10 steps, the input influences the machine in a non-linear way
            uint64_t input_mod = (step_index > 10) ? (real_state & 0xF) : 0;
            uint64_t effective_op = base_op + input_mod;

            shadow_state = ((shadow_state >> 19) | (shadow_state << 45)) ^ unseen_table[effective_op % 256];
            shadow_state = shadow_state * 0x3141592653589793ULL + (uint64_t)step_index;

            uint8_t mix = (uint8_t)(real_state ^ shadow_state ^ path_entropy);
            
            real_state = ((real_state << 13) | (real_state >> 51)) + unseen_table[mix];
            real_state = (real_state * 0x5bd1e9955bd1e995ULL) + effective_op;

            // FITNA UPGRADE 4: Environment Coupling (Stack Pointer influence)
            // Note: In a real elite chall, we'd use RSP, but for stability we use step_index.
            path_entropy = ((path_entropy << 7) | (path_entropy >> 57)) ^ real_state ^ shadow_state;

            if (((real_state ^ shadow_state) & 0x0F0F0F) == 0x0A0A0A) {
                abyss_mode = 1;
            }
        }

        uc->uc_mcontext.gregs[REG_RIP] += 2;
    }
}

void execute_command(uint64_t base_op) {
    __asm__ volatile(
        "mov %0, %%r8\n\t"
        "ud2\n\t"
        : 
        : "r" (base_op)
        : "%r8"
    );
}

__attribute__((destructor)) void final_judgment() {
    uint64_t key = real_state ^ shadow_state ^ path_entropy;
    unsigned char decrypted[sizeof(encrypted_flag) + 1];

    for (size_t i = 0; i < sizeof(encrypted_flag); i++) {
        decrypted[i] = encrypted_flag[i] ^ ((key >> ((i % 8) * 8)) & 0xFF);
    }
    decrypted[sizeof(encrypted_flag)] = '\0';
    
    if (decrypted[0] == 'N' && decrypted[1] == 'S' && decrypted[2] == 'C') {
        puts("\n[+] The Abyss has spoken.");
        puts((char *)decrypted);
    }
}

static void normalize_inplace(char *s) {
    size_t len = strlen(s);
    while (len && (s[len-1] == '\n' || s[len-1] == '\r')) {
        s[--len] = '\0';
    }
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = abyss_handler;
    sa.sa_flags = SA_SIGINFO;
    sigaction(SIGILL, &sa, NULL);

    perform_ablution();

    puts(banner);
    puts("(!) Only the righteous path leads out of the Abyss.\n");

    char line[256];
    while (1) {
        fputs("aitssi-os> ", stdout);
        fflush(stdout);

        if (!fgets(line, sizeof(line), stdin)) break;
        normalize_inplace(line);

        if (line[0] == '\0') continue;
        if (strcmp(line, "exit") == 0) break;

        uint64_t op = 0;
        if (strncmp(line, "zikr", 4) == 0) op = 1;
        else if (strncmp(line, "salat", 5) == 0) op = 2;
        else if (strncmp(line, "siyam", 5) == 0) op = 3;
        else if (strncmp(line, "zakat", 5) == 0) op = 4;
        else if (strncmp(line, "haj", 3) == 0) op = 5;
        else if (strncmp(line, "dua", 3) == 0) op = 6;
        else if (strncmp(line, "niyah", 5) == 0) op = 7;
        else {
            puts("command not found");
            continue;
        }

        execute_command(op);
    }

    return 0;
}
