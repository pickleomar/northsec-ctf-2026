# solver.py - AITSSI-OS Fitna Tier Solver
# Replicates the 9.5/10 branching state machine with Fitna upgrades.

def rol64(x, n):
    return ((x << n) & 0xFFFFFFFFFFFFFFFF) | (x >> (64 - n))

def ror64(x, n):
    return ((x >> n) | (x << (64 - n))) & 0xFFFFFFFFFFFFFFFF

def solve():
    # 1. Replicate Mirror-Trap-Aware unseen_table generation
    # Assumption: Not traced (trap_seed = 0)
    trap_seed = 0
    seed = 0xfeedc0de1337beef ^ trap_seed
    unseen_table = []
    for _ in range(256):
        seed ^= (seed << 13) & 0xFFFFFFFFFFFFFFFF
        seed ^= (seed >> 7)
        seed ^= (seed << 17) & 0xFFFFFFFFFFFFFFFF
        unseen_table.append(seed)

    # 2. Fitna Data
    encrypted_flag = [
        0x41, 0xc2, 0x3c, 0x95, 0x54, 0x60, 0xa3, 0x89, 0x50, 0xf7, 0x4c, 0x85, 
        0x4b, 0x36, 0x80, 0x93, 0x64, 0xce, 0x4b, 0x85, 0x4b, 0x65, 0xf1, 0xbe, 
        0x62, 0xa1, 0xa, 0xdc, 0x4e, 0x65, 0xae, 0x9c
    ]

    # Initial states
    real_state = unseen_table[0]
    shadow_state = 0xdeadbeef12345678
    path_entropy = 0xc0deba5e
    
    # 3. The righteous path (Only 10 steps to stay in the pre-lex-change zone for simplicity)
    # Note: To fully solve Fitna (31 steps), the solver must track the state-dependent lex mod.
    target_sequence = [1, 2, 1, 3, 1, 4, 1, 5, 2, 2, 6, 1, 7, 3, 3, 1, 2, 4, 5, 6, 1, 1, 2, 3, 4, 5, 6, 7, 1, 2, 1]

    for step_index in range(1, 32):
        base_op = target_sequence[step_index-1]
        
        # FITNA UPGRADE 3: State-Dependent Command Lexing
        input_mod = (real_state & 0xF) if step_index > 10 else 0
        effective_op = base_op + input_mod

        # Shadow Update
        shadow_state = (ror64(shadow_state, 19) ^ (unseen_table[effective_op % 256])) & 0xFFFFFFFFFFFFFFFF
        shadow_state = (shadow_state * 0x3141592653589793 + step_index) & 0xFFFFFFFFFFFFFFFF
        
        # Real Update (Branching)
        mix = (real_state ^ shadow_state ^ path_entropy) & 0xFF
        real_state = (rol64(real_state, 13) + unseen_table[mix]) & 0xFFFFFFFFFFFFFFFF
        real_state = (real_state * 0x5bd1e9955bd1e995 + effective_op) & 0xFFFFFFFFFFFFFFFF
        
        # Entropy Coupling
        path_entropy = (rol64(path_entropy, 7) ^ real_state ^ shadow_state) & 0xFFFFFFFFFFFFFFFF

    # 4. Decryption
    key = real_state ^ shadow_state ^ path_entropy
    decrypted = ""
    for i in range(len(encrypted_flag)):
        byte = encrypted_flag[i] ^ ((key >> ((i % 8) * 8)) & 0xFF)
        decrypted += chr(byte)
    
    print(f"[+] Final States: R={hex(real_state)} S={hex(shadow_state)} E={hex(path_entropy)}")
    print(f"[+] Decrypted Flag: {decrypted}")

if __name__ == "__main__":
    solve()
