#include <stdio.h>
#include <string.h>
#include <unistd.h>

// Encrypted Flag: NSC{m3m0ry_dump_plu5_runt1m3_d3crypt10n}
// Key: 0xdeadcode (DE AD C0 DE)
unsigned char encrypted_flag[] = { 
    0x90, 0xfe, 0x83, 0xa5, 0xb3, 0x9e, 0xad, 0xee, 
    0xac, 0xd4, 0x9f, 0xba, 0xab, 0xc0, 0xb0, 0x81, 
    0xae, 0xc1, 0xb5, 0xeb, 0x81, 0xdf, 0xb5, 0xb0, 
    0xaa, 0x9c, 0xad, 0xed, 0x81, 0xc9, 0xf3, 0xbd, 
    0xac, 0xd4, 0xb0, 0xaa, 0xef, 0x9d, 0xae, 0xa3, 
    0x00 
};

// We store the key as a byte array to ensure consistent order (DE AD C0 DE)
// regardless of system endianness (Little Endian vs Big Endian).
unsigned char key[] = { 0xde, 0xad, 0xc0, 0xde };
/*
void decrypt_flag(unsigned char *buffer, int len, unsigned char *k, int k_len) {
    for (int i = 0; i < len; i++) {
        // XOR the current byte with the corresponding key byte (cycling)
        buffer[i] = buffer[i] ^ k[i % k_len];
    }
}
*/
int main() {
    printf("========================================\n");
    printf("      SECURE PAYLOAD SYSTEM LOADED      \n");
    printf("========================================\n");
    
    printf("Decrypting secure content...\n");
    sleep(1); 
    
    // Calculate lengths
    int flag_len = strlen((char *)encrypted_flag);
    int key_len = sizeof(key);

    // Decrypt in place
//    decrypt_flag(encrypted_flag, flag_len, key, key_len);
    
//    printf("Success! The secret is:\n");
//    printf("%s\n", encrypted_flag);
    
    // Wipe memory for safety
    memset(encrypted_flag, 0, flag_len);
    
    return 0;
}
