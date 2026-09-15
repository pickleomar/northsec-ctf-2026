org 100h

section .text
start:
    ; --- 1. Display Prompt (Plaintext is fine for the prompt) ---
    mov dx, prompt_msg
    mov ah, 09h
    int 21h

    ; --- 2. Fake Input Check ---
    mov dx, input_buffer
    mov ah, 0Ah
    int 21h

    ; New line
    mov dx, newline
    mov ah, 09h
    int 21h

    ; --- 3. Runtime Decrypt & Print ---

    ; === PATH A: IBM PC (Standard DOSBox) ===
    ; Target: 0xB800 (VGA Text)
    mov ax, 0B800h
    mov es, ax
    xor di, di          
    mov si, fake_enc    ; Load address of ENCRYPTED fake message
    call print_ibm_xor  ; Decrypts on the fly

    ; === PATH B: NEC PC-98 (DOSBox-X) ===
    ; Target: 0xA000 (PC-98 Text)
    mov ax, 0A000h
    mov es, ax
    xor di, di          
    mov si, real_enc    ; Load address of ENCRYPTED flag
    call print_pc98_xor ; Decrypts on the fly

hang:
    jmp hang

; ---------------------------------------------------------
; Subroutine: Decrypt & Print to IBM PC (0xB800)
; ---------------------------------------------------------
print_ibm_xor:
    push si
    push di
.loop:
    lodsb               ; Load encrypted byte into AL
    cmp al, 0           ; Check for end of string (0x00)
    jz .done
    
    ; >>> RUNTIME DECRYPTION <<<
    xor al, 0x37        ; The Key is 0x37
    ; >>> END DECRYPTION <<<

    stosb               ; Store Decrypted Char to VRAM [ES:DI]
    mov al, 0x4F        ; Attribute (Red Background)
    stosb               ; Store Attribute
    jmp .loop
.done:
    pop di
    pop si
    ret

; ---------------------------------------------------------
; Subroutine: Decrypt & Print to PC-98 (0xA000)
; ---------------------------------------------------------
print_pc98_xor:
    push si
    push di
.loop:
    lodsb               ; Load encrypted byte into AL
    cmp al, 0           ; Check for end of string
    jz .done

    ; >>> RUNTIME DECRYPTION <<<
    xor al, 0x37        ; The Key is 0x37
    ; >>> END DECRYPTION <<<

    stosb               ; Store Decrypted Char to VRAM [ES:DI]
    inc di              ; Skip Attribute byte (Standard for PC-98)
    inc di              ; Move to next char
    jmp .loop
.done:
    pop di
    pop si
    ret

section .data
    prompt_msg   db 'root@legacy-system:~# ./auth_check', 0Dh, 0Ah
                 db '[SYSTEM] Enter Authorization Code: $'
    newline      db 0Dh, 0Ah, '$'
    input_buffer db 64, 0
                 times 64 db 0

    ; NOTE: These are RAW hex bytes. No strings are visible here.
    ; Key used: 0x37

    ; "IDENTITY CONFIRMED. Flag: NSC{0xA000_VRAM_M4ST3R}" (XOR 0x37)
    real_enc db 0x7e, 0x73, 0x72, 0x79, 0x63, 0x7e, 0x63, 0x6e, 0x17, 0x74, 0x78, 0x79, 0x71, 0x7e, 0x65, 0x7a, 0x72, 0x73, 0x19, 0x17, 0x71, 0x5b, 0x56, 0x50, 0xd, 0x17, 0x79, 0x64, 0x74, 0x4c, 0x7, 0x4f, 0x76, 0x7, 0x7, 0x7, 0x68, 0x61, 0x65, 0x76, 0x7a, 0x68, 0x7a, 0x3, 0x64, 0x63, 0x4, 0x65, 0x4a, 0x00

    ; "ERROR: HARDWARE ID MISMATCH. ACCESS DENIED." (XOR 0x37)
    fake_enc db 0x72, 0x65, 0x65, 0x78, 0x65, 0xd, 0x17, 0x7f, 0x76, 0x65, 0x73, 0x60, 0x76, 0x65, 0x72, 0x17, 0x7e, 0x73, 0x17, 0x7a, 0x7e, 0x64, 0x7a, 0x76, 0x63, 0x74, 0x7f, 0x19, 0x17, 0x76, 0x74, 0x74, 0x72, 0x64, 0x64, 0x17, 0x73, 0x72, 0x79, 0x7e, 0x72, 0x73, 0x19, 0x00
