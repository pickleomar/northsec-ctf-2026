use sha2::{Digest, Sha256};
use std::hint::black_box;
use std::io;
use std::sync::atomic::{AtomicPtr, Ordering};

// Global pointer to the VM for the signal handler
static VM_PTR: AtomicPtr<VM> = AtomicPtr::new(std::ptr::null_mut());
static HISTORY_PTR: AtomicPtr<History> = AtomicPtr::new(std::ptr::null_mut());

// ============================================================================
// BANNER
// ============================================================================

#[allow(dead_code)]
pub fn print_banner() {
    print!(
r#"$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$                                                                            $$
$$  Welcome To...                                                             $$
$$   _____  _____  _____  _____  _   _  _____                                 $$
$$  /  __ \|  _  |/  ___||_   _|| \ | ||  _  |                                $$
$$  | /  \/| | | |\ `--.   | |  |  \| || | | |                                $$
$$  | |    | |_| | `--. \  | |  | . ` || | | |                                $$
$$  | \__/\|  _  |/\__/ / _| |_ | |\  |\ \_/ /                                $$
$$   \____/|_| |_|\____/  \___/ \_| \_/ \___/                                 $$
$$                                                                            $$
$$              _____ ______   ___  _   _  _____  ___                         $$
$$             /  ___||  ___| / _ \| | | ||  __ \/ _ \                        $$
$$             \ `--. | |_   / /_\ \ | | || |  \/ /_\ \                       $$
$$              `--. \|  _|  |  _  || | || | __ |  _  |                       $$
$$             /\__/ /| |    | | | || |_| || |_\ \ | | |                      $$
$$             \____/ \_|    \_| |_/\___/  \____/_| |_|                      $$
$$                                                                            $$
$$ ========================================================================== $$
$$                                                                            $$
$$        * * ,;;;;;;;;;,            * * $$
$$    [7][7][7]             ,;;;;;;;;;;;;;             [ $ ]                  $$
$$                        ,;;   _     _   ;;,            |                    $$
$$                       ,;;   (O)   (O)   ;;,         __|__                  $$
$$                       ;;;      | |      ;;;        /_____\                 $$
$$                       ;;;      |_|      ;;;                                $$
$$                       ;;;   [ _|_|_ ]   ;;;    <--[HAHAAAAYOO]              $$
$$                        ';;      ^      ;;'                                 $$
$$                          ';;_________;;'                                   $$
$$                             /       \                                      $$
$$                           //|   |   |\\                                    $$
$$        _______          _// |   |   | \\_          _______                 $$
$$       |   A   |        | |  |   |   | |        |   K   |                    $$
$$       |  <3   |        | |  |___|___|  | |        |   <>  |                $$
$$       |_______|        |_|             |_|        |_______|                $$
$$                                                                            $$
$$                                                                            $$
$$        ___   _      ___     _____  _   _  _____                            $$
$$       / _ \ | |    / _ \   |  _  || \ | ||  ___|                           $$
$$      / /_\ \| |   / /_\ \  | | | ||  \| || |__                             $$
$$      |  _  || |   |  _  |  | | | || . ` ||  __|                            $$
$$      | | | || |___| | | |  \ \_/ /| |\  || |___                            $$
$$      \_| |_/\____/\_| |_/   \___/ \_| \_/\____/                            $$
$$                                                                            $$
$$              ___   _      ___     _____  _    _  _____                     $$
$$             / _ \ | |    / _ \   |_   _|| |  | ||  _  |                    $$
$$            / /_\ \| |   / /_\ \    | |  | |  | || | | |                    $$
$$            |  _  || |   |  _  |    | |  | |/\| || | | |                    $$
$$            | | | || |___| | | |    | |  \  /\  /\ \_/ /                    $$
$$            \_| |_/\____/\_| |_/    \_/   \/  \/  \___/                     $$
$$  remarque: if you bust you restart we love to give second chances          $$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
"#
    );
}

// ============================================================
// SIGNAL HANDLER (HIDDEN EXECUTION LAYER)
// ============================================================

#[cfg(target_os = "linux")]
extern "C" fn sigill_handler(_sig: i32, _info: *mut libc::siginfo_t, context: *mut libc::c_void) {
    let vm_ptr = VM_PTR.load(Ordering::SeqCst);
    let history_ptr = HISTORY_PTR.load(Ordering::SeqCst);

    if !vm_ptr.is_null() && !history_ptr.is_null() {
        unsafe {
            let vm = &mut *vm_ptr;
            let history = &*history_ptr;
            
            // Execute one step of the VM logic
            vm.step(history);

            // Advance the instruction pointer to skip the 'ud2' (2 bytes)
            let ucontext = context as *mut libc::ucontext_t;
            #[cfg(target_arch = "x86_64")]
            {
                (*ucontext).uc_mcontext.gregs[libc::REG_RIP as usize] += 2;
            }
            #[cfg(target_arch = "aarch64")]
            {
                (*ucontext).uc_mcontext.pc += 4;
            }
        }
    }
}

fn setup_signal_handler() {
    #[cfg(target_os = "linux")]
    unsafe {
        let mut sa: libc::sigaction = std::mem::zeroed();
        sa.sa_sigaction = sigill_handler as *const () as usize;
        sa.sa_flags = libc::SA_SIGINFO;
        libc::sigaction(libc::SIGILL, &sa, std::ptr::null_mut());
    }
}

// ============================================================
// ANTI DEBUG
// ============================================================

// Returns true if a debugger is detected
fn is_debugged() -> bool {
    #[cfg(target_os = "linux")]
    unsafe {
        if libc::ptrace(libc::PTRACE_TRACEME, 0, 1, 0) == -1 {
            return true;
        }
    }
    false
}

// ============================================================
// HISTORY
// ============================================================

#[derive(Clone)]
struct History {
    mask: u64,
    ops: u64,
}

impl History {
    fn new() -> Self {
        Self {
            mask: 0xA5A5_F00D_CAFE_BEEF, // Magic initial mask
            ops: 0,
        }
    }

    // Records an operation (like deal/hit/stand) into the history mask with its associated value
    fn push(&mut self, action: u8, value: u32) {
        self.ops += 1;
        // Combine action and value into a 64-bit chunk
        let combo = ((action as u64) << 32) | (value as u64);
        // Shift and XOR based on operation count to ensure order dependence
        self.mask ^= combo.rotate_left((self.ops % 61) as u32);
        // Scramble the mask using a large prime multiplier
        self.mask = self.mask.wrapping_mul(0x9E37_79B9_7F4A_7C15);
        // Additional mixing step
        self.mask ^= self.mask >> 31;
    }

    // Creates the final history hash to be used for state unlock
    fn finalize(&self) -> u64 {
        // XOR mask with scrambled ops counter and a secondary constant
        let mut x = self.mask ^ self.ops.wrapping_mul(0x1337BEEF);

        // Mix the hash using shifts and large prime multiplications (MurmurHash3-style finalizer)
        x ^= x >> 33;
        x = x.wrapping_mul(0xff51afd7ed558ccd);
        x ^= x >> 33;
        x = x.wrapping_mul(0xc4ceb9fe1a85ec53);
        x ^= x >> 33;

        x
    }
}

// ============================================================
// CASINO
// ============================================================

struct Casino {
    rounds: u64,
    hits: u64,
    busts: u64,
    rng: u64,
    player: u32,
    dealer: u32,
    history: History,
    hidden: u64,
}

impl Casino {
    fn new() -> Self {
        Self {
            rounds: 0,
            hits: 0,
            busts: 0,
            rng: 0x9e3779b97f4a7c15, // LCG / Xorshift initial seed
            player: 0,
            dealer: 0,
            history: History::new(),
            hidden: 0xD1CEB00B_F00D_C0DE, // Initial hidden state
        }
    }

    // Custom RNG implementation (Xorshift variant with deterministic "fake entropy")
    fn next(&mut self) -> u32 {
        let mut x = self.rng;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;

        // 🔥 Deterministic "Fake Entropy"
        let entropy = self.rounds.wrapping_mul(0x9E3779B9) 
                    ^ self.hits.wrapping_add(self.busts << 16);
        x ^= entropy;

        self.rng = x;
        // Output scrambling
        (x.wrapping_mul(0x2545F4914F6CDD1D) >> 32) as u32
    }

    // Deal cards (value between 12 and 21)
    fn deal(&mut self) -> u32 {
        (self.next() % 10) + 12
    }

    // Draw card (value between 1 and 10)
    fn draw(&mut self) -> u32 {
        (self.next() % 10) + 1
    }

    // Main game logic for a single round
    fn round(&mut self) {
        self.rounds += 1;

        self.player = self.deal();
        self.dealer = self.deal();

        // Record initial deals (Action 1)
        self.history.push(1, self.player);
        self.history.push(1, self.dealer);

        loop {
            println!("Player: {} | Dealer: {}", self.player, self.dealer / 2);
            println!("(h)it (s)tand (q)uit");

            let mut i = String::new();
            io::stdin().read_line(&mut i).unwrap();
            let c = i.trim();

            if c == "q" {
                std::process::exit(0);
            }

            if c == "h" {
                let card = self.draw();
                self.player += card;
                self.history.push(2, card);
                self.hits += 1;

                if self.player > 21 {
                    self.history.push(4, self.player);
                    self.busts += 1;
                    return; 
                }
            } else {
                self.history.push(3, self.player);
                break;
            }
        }

        self.hidden ^= (self.player as u64)
            .wrapping_add(self.rounds << 3)
            .rotate_left((self.hits % 16) as u32);

        self.hidden = self.hidden.wrapping_mul(0x9E37_79B9_7F4A_7C15);

        if self.player > self.dealer {
            self.dealer = self.player + 1;
        }
    }

    fn trigger(&self) -> bool {
        self.rounds > 6
            && self.busts >= 3
            && (self.history.finalize() & 0xFFFF_FFFF) == 0x1337_C0DE
    }
}

// ============================================================
// UNPACKER
// ============================================================

fn unpack(mut state: u32) -> Vec<u8> {
    let base = vec![
        0x11,0x22,0x33,0x44,0xAA,
        0x55,0x66,0x77,0x88,0x99,
        0xAB,0xCD,0xEF,0x13,0x37,
    ];

    let mut code = vec![0u8; base.len()];
    let mut prev: u8 = 0xC3; 
    let mut t: u32 = 0xC0FFEE12; 

    for i in 0..base.len() {
        state ^= state.wrapping_mul(0x6D2B79F5);
        state ^= state.rotate_left(11).wrapping_add(t);
        t = t.wrapping_mul(0x45D9F3B)
            ^ state.rotate_right((i as u32) & 31);
        let key = ((state ^ t ^ (prev as u32)) >> ((i % 5) + 3)) as u8;
        let idx = i as u8;
        let b = (base[i] as u32).wrapping_add(idx as u32) as u8 ^ key ^ prev;
        prev = b.rotate_left((state % 7) as u32) ^ (t as u8);
        code[i] = b;
    }
    code
}

// ============================================================
// VM
// ============================================================

struct VM {
    regs: [u32; 8],        
    state: u32,            
    shadow_state: u32,     
    trace: u32,            
    pc: usize,             
    code: Vec<u8>,         
    fingerprint: u32,      
    last_op: u8,
    stall: u32,
    exec_noise: u8,
}

impl VM {
    fn new(state: u32) -> Self {
        Self {
            regs: [0; 8],
            state,
            shadow_state: state ^ 0x5555AAAA, 
            trace: 0,
            pc: 0,
            code: unpack(state),
            fingerprint: 0x1337C0DE,
            last_op: 0,
            stall: 0,
            exec_noise: 0x5A,
        }
    }

    fn step(&mut self, history: &History) {
        if is_debugged() {
            self.state = self.state.wrapping_mul(0xBADB_AD01);
            self.shadow_state ^= 0xBADB_AD00;
            self.fingerprint ^= 0xDEADC0DE;
        }

        let mut op = self.code[self.pc % self.code.len()];
        op ^= self.state as u8;
        op ^= self.exec_noise;
        self.pc += 1;
        let effective_op = op ^ (self.state as u8 & 0x07);

        if self.last_op == op {
            self.stall ^= self.trace;
            self.state ^= self.stall.rotate_left(3);
        }

        match effective_op {
            0x11 => self.regs[0] ^= self.regs[1],
            0x22 => self.regs[1] = self.regs[1].wrapping_add(3),
            0x33 => self.regs[2] ^= 0x1337,
            0x44 => self.regs[3] = self.regs[3].wrapping_mul(3),
            0x55 => self.regs[4] = self.regs[4].rotate_left(1),
            0x66 => {
                if self.trace.wrapping_add(self.stall) & 3 == 0 {
                    self.regs[5] ^= self.trace ^ self.state;
                } else {
                    self.regs[5] ^= self.trace.rotate_left(1);
                }
            }
            0x77 => self.regs[6] = self.regs[6].wrapping_add(self.state),
            0x88 => self.regs[7] ^= self.regs[0],
            0xAA => {
                if self.trace & 1 == 0 {
                    self.regs[0] ^= 0xDEADBEEF;
                }
            }
            _ => {
                self.shadow_state = self.shadow_state.wrapping_add(effective_op as u32);
            }
        }

        self.last_op = op;
        if self.pc % 7 == 0 {
            self.state ^= (history.finalize() & 0xFFFFFFFF) as u32;
        }
        let jitter = (self.state ^ self.trace) & 3;
        if jitter == 0 {
            let fake_env = (self.trace ^ self.state ^ 0xDEADBEEF) & 0xFFFF;
            self.state ^= fake_env;
        }
        self.trace = self.trace.rotate_left(5) ^ op as u32;
        self.shadow_state = self.shadow_state.rotate_right(1) ^ self.trace;
        let idx = (self.state as usize) % self.code.len();
        self.code[idx] ^= op.wrapping_add(self.trace as u8);
        self.state ^= self.trace;
        self.state = self.state.rotate_right(3);
        self.exec_noise = self.exec_noise.wrapping_mul(31) ^ (self.trace as u8);
        self.fingerprint ^= self.trace.rotate_left(self.pc as u32);
        self.fingerprint = self.fingerprint.wrapping_mul(0x45d9f3b);
    }

    fn run(&mut self, history: &History) {
        VM_PTR.store(self as *mut _, Ordering::SeqCst);
        HISTORY_PTR.store(history as *const _ as *mut _, Ordering::SeqCst);
        let steps = 64 + (self.state & 31);
        for _ in 0..steps {
            unsafe {
                #[cfg(target_arch = "x86_64")]
                std::arch::asm!("ud2");
                #[cfg(target_arch = "aarch64")]
                std::arch::asm!(".word 0x00000000"); 
                #[cfg(not(any(target_arch = "x86_64", target_arch = "aarch64")))]
                self.step(history);
            }
        }
        VM_PTR.store(std::ptr::null_mut(), Ordering::SeqCst);
        HISTORY_PTR.store(std::ptr::null_mut(), Ordering::SeqCst);
    }

    fn key(&self, history: u64, game_seed: u32) -> [u8; 32] {
        let mut h = Sha256::new();
        for r in &self.regs { h.update(r.to_le_bytes()); }
        h.update(self.state.to_le_bytes());
        h.update(self.shadow_state.to_le_bytes());
        h.update(self.trace.to_le_bytes());
        h.update(history.to_le_bytes());
        h.update(game_seed.to_le_bytes());
        h.update(self.fingerprint.to_le_bytes());
        h.finalize().into()
    }
}

const ENC: &[u8] = &[
    162, 99, 50, 64, 220, 176, 133, 37, 18, 146, 89, 134, 158, 252, 27, 153,
    108, 246, 232, 105, 33, 227, 203, 216, 205, 102, 209, 8, 179, 43, 221, 240
];

fn main() {
    print_banner();
    setup_signal_handler();
    let _ = is_debugged();
    let mut game = Casino::new();
    loop {
        game.round();
        if game.trigger() {
            println!("[*] unlocked state");
            let mut h_hasher = Sha256::new();
            h_hasher.update(game.rounds.to_le_bytes());
            h_hasher.update(game.hits.to_le_bytes());
            h_hasher.update(game.busts.to_le_bytes());
            h_hasher.update(game.history.finalize().to_le_bytes());
            h_hasher.update(game.hidden.to_le_bytes());
            let init_bytes = h_hasher.finalize();
            let mut init = u32::from_le_bytes(init_bytes[0..4].try_into().unwrap());
            init ^= init.rotate_left(11);
            init = init.wrapping_mul(0x9E3779B1);
            init ^= init >> 16;
            init = init.rotate_left((game.busts % 32) as u32);
            black_box(init);
            let mut vm = VM::new(init);
            vm.run(&game.history);
            let history = game.history.finalize();
            let key = vm.key(history, init);
            let out: Vec<u8> = ENC.iter()
                .enumerate()
                .map(|(i, b)| b ^ key[i % 32])
                .collect();
            let mut h_final = 0u32;
            for &b in &out {
                h_final = h_final.wrapping_add(b as u32);
                h_final = h_final.rotate_left(7) ^ 0x55AAAA55;
            }
            if out.starts_with(b"NSC{") && h_final == 0x58A07EB2 {
                println!("waa rbahatoo: {}", String::from_utf8_lossy(&out));
            } else {
                let mut fake_flag = String::from("NSC{");
                for i in 0..out.len().saturating_sub(5) {
                    let char = b"0123456789abcdef"[(h_final.wrapping_add(i as u32) % 16) as usize] as char;
                    fake_flag.push(char);
                }
                fake_flag.push('}');
                println!("waa rbahatoo: {}", fake_flag);
                println!("marra jaya inchaallah");
            }
            break; 
        }
    }
}
