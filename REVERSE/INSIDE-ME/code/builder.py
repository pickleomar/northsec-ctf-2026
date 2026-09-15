import sys
import random

def generate_calculator_host(payload_bytes):
    # Convert payload to C hex array
    c_array = ", ".join([f"0x{b:02x}" for b in payload_bytes])
    
    # Configuration for the "Memory Leak"
    # We allocate 150MB to make it obvious in Task Manager / top
    ALLOC_SIZE = 150 * 1024 * 1024 
    
    # Hide the payload at a random offset deep inside the 150MB
    # (e.g., somewhere after 100MB)
    PAYLOAD_OFFSET = 100 * 1024 * 1024 + random.randint(0, 4096)

    code = f"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// ---------------------------------------------------------
// HIDDEN DATA SECTION
// This array contains the 'payload.bin' bytes
// ---------------------------------------------------------
unsigned char hidden_data[] = {{ {c_array} }};

// Global pointer to our "working memory"
char *calculator_memory;

void print_banner() {{
    printf("========================================\\n");
    printf("      SUPER FAST MATH CALCULATOR v1.0   \\n");
    printf("========================================\\n");
}}

void show_menu() {{
    printf("\\n--- Menu ---\\n");
    printf("1. Add Numbers\\n");
    printf("2. Subtract Numbers\\n");
    printf("3. View Optimization Tips\\n");
    printf("4. Exit\\n");
    printf("Choice: ");
}}

// This function initializes the "Calculator Memory"
// It intentionally allocates WAY too much memory (150MB)
void init_calculator() {{
    printf("[*] Initializing high-performance math engine...\\n");
    
    // THE LEAK: Allocating 150MB for a simple calculator
    calculator_memory = (char *)malloc({ALLOC_SIZE});
    
    if (!calculator_memory) {{
        printf("Error: Could not allocate memory for calculator!\\n");
        exit(1);
    }}

    // Fill it with junk (0x90 NOPs) so it looks like it's being used
    memset(calculator_memory, 0x90, {ALLOC_SIZE});

    // SILENT INJECTION: Copy the hidden payload into the allocated heap
    // It sits at offset {PAYLOAD_OFFSET}, doing nothing.
    memcpy(calculator_memory + {PAYLOAD_OFFSET}, hidden_data, sizeof(hidden_data));
    
    printf("[*] Engine Ready. PID: %d\\n", getpid());
}}

void do_math(int mode) {{
    double a, b, result;
    printf("\\nEnter first number: ");
    if (scanf("%lf", &a) != 1) {{
        while(getchar() != '\\n'); // clean buffer
        return; 
    }}
    printf("Enter second number: ");
    if (scanf("%lf", &b) != 1) {{
        while(getchar() != '\\n'); // clean buffer
        return;
    }}

    if (mode == 1) result = a + b;
    else result = a - b;

    printf(">> RESULT: %.2f\\n", result);
}}

int main() {{
    // Disable buffering
    setvbuf(stdout, NULL, _IONBF, 0);

    init_calculator();
    print_banner();

    int choice;
    while(1) {{
        show_menu();
        if (scanf("%d", &choice) != 1) break;

        switch(choice) {{
            case 1:
                do_math(1);
                break;
            case 2:
                do_math(2);
                break;
            case 3:
                // THE HINT
                printf("\\n[TIP] Performance Hint:\\n");
                printf("       A clean program always must use and allocate the minimal resource to work with.\\n");
                printf("       (Wait... why is this calculator using 150MB of RAM?)\\n");
                break;
            case 4:
                printf("Exiting...\\n");
                free(calculator_memory);
                return 0;
            default:
                printf("Invalid option.\\n");
        }}
    }}
    return 0;
}}
"""
    return code

if __name__ == "__main__":
    try:
        # Read the payload.bin file
        with open("payload.bin", "rb") as f:
            data = f.read()
        
        print(f"[+] Read {{len(data)}} bytes from payload.bin")
        
        # Generate the C code
        c_code = generate_calculator_host(data)
        
        # Save to challenge.c
        with open("challenge.c", "w") as f:
            f.write(c_code)
            
        print("[+] 'challenge.c' created successfully.")
        print("[+] Compile command: gcc challenge.c -o math_calculator")
        
    except FileNotFoundError:
        print("[-] Error: 'payload.bin' not found. Make sure you generated it first!")
