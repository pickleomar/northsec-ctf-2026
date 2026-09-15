use sha2::{Digest, Sha256};
use std::sync::atomic::{AtomicBool, Ordering};
use std::process::exit;
use rayon::prelude::*;

fn rol64(v: u64, n: u32) -> u64 {
    v.rotate_left(n % 64)
}
fn umul64(a: u64, b: u64) -> u64 {
    a.wrapping_mul(b)
}
fn umul32(a: u32, b: u32) -> u32 {
    a.wrapping_mul(b)
}
fn rol32(v: u32, n: u32) -> u32 {
    v.rotate_left(n % 32)
}
fn ror32(v: u32, n: u32) -> u32 {
    v.rotate_right(n % 32)
}
fn rol8(v: u8, n: u32) -> u8 {
    v.rotate_left(n % 8)
}

const K1: u64 = 0x9E37_79B9_7F4A_7C15;
const TARGET: u64 = 0x1337_C0DE;
const ENC: [u8; 32] = [
    162, 99, 50, 64, 220, 176, 133, 37, 18, 146, 89, 134, 158, 252, 27, 153,
    108, 246, 232, 105, 33, 227, 203, 216, 205, 102, 209, 8, 179, 43, 221, 240
];

#[derive(Clone)]
struct GameState {
    mask: u64,
    ops: u64,
    total_hits: u64,
    total_busts: u64,
    hidden: u64,
    player: u32,
    rng: u64,
}

impl GameState {
    fn new() -> Self {
        Self {
            mask: 0xA5A5_F00D_CAFE_BEEF,
            ops: 0,
            total_hits: 0,
            total_busts: 0,
            hidden: 0xD1CEB00B_F00D_C0DE,
            player: 0,
            rng: 0x9e3779b97f4a7c15,
        }
    }

    fn next(&mut self, round_count: u64) -> u32 {
        let mut x = self.rng;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;

        let entropy = round_count.wrapping_mul(0x9E3779B9) 
                    ^ self.total_hits.wrapping_add(self.total_busts << 16);
        x ^= entropy;

        self.rng = x;
        (x.wrapping_mul(0x2545F4914F6CDD1D) >> 32) as u32
    }

    fn push_history(&mut self, action: u8, value: u32) {
        self.ops += 1;
        let combo = ((action as u64) << 32) | (value as u64);
        self.mask ^= combo.rotate_left((self.ops % 61) as u32);
        self.mask = self.mask.wrapping_mul(K1);
        self.mask ^= self.mask >> 31;
    }

    fn deal_round(&mut self, round_count: u64) {
        let p_val = (self.next(round_count) % 10) + 12;
        let d_val = (self.next(round_count) % 10) + 12;

        self.push_history(1, p_val);
        self.push_history(1, d_val);

        self.player = p_val;
    }

    fn draw_card(&mut self, round_count: u64) -> u32 {
        let card_val = (self.next(round_count) % 10) + 1;
        self.player += card_val;
        self.push_history(2, card_val);
        self.total_hits += 1;
        card_val
    }

    fn bust(&mut self) {
        self.push_history(4, self.player);
        self.total_busts += 1;
    }

    fn stand(&mut self) {
        self.push_history(3, self.player);
    }

    fn end_round(&mut self, round_count: u64) {
        self.hidden ^= (self.player as u64)
            .wrapping_add(round_count << 3)
            .rotate_left((self.total_hits % 16) as u32);
        self.hidden = self.hidden.wrapping_mul(K1);
    }

    fn finalize(&self) -> u64 {
        let mut x = self.mask ^ self.ops.wrapping_mul(0x1337BEEF);
        x ^= x >> 33;
        x = x.wrapping_mul(0xFF51AFD7ED558CCD);
        x ^= x >> 33;
        x = x.wrapping_mul(0xC4CEB9FE1A85EC53);
        x ^= x >> 33;
        x
    }
}

static FOUND: AtomicBool = AtomicBool::new(false);

fn explore(state: GameState, round_count: u64, max_rounds: u64) {
    if FOUND.load(Ordering::Relaxed) { return; }

    if round_count > max_rounds {
        let hv = state.finalize();
        if (hv & 0xFFFFFFFF) == TARGET && state.total_busts >= 3 {
            check_vm(state, round_count - 1);
        }
        return;
    }

    let mut round_state = state.clone();
    round_state.deal_round(round_count);

    // Option 1: Stand immediately
    {
        let mut s = round_state.clone();
        s.stand();
        s.end_round(round_count);
        explore(s, round_count + 1, max_rounds);
    }

    // Option 2: Hit one or more times
    {
        let mut h = round_state.clone();
        while h.player <= 21 {
            h.draw_card(round_count);
            if h.player > 21 {
                // Forced bust
                let mut b = h.clone();
                b.bust();
                b.end_round(round_count);
                explore(b, round_count + 1, max_rounds);
                break;
            } else {
                // Choice: Stand now
                let mut s = h.clone();
                s.stand();
                s.end_round(round_count);
                explore(s, round_count + 1, max_rounds);
                // Or continue hitting (loop continues)
            }
        }
    }
}

fn check_vm(final_state: GameState, rounds: u64) {
    let hv = final_state.finalize();
    let th = final_state.total_hits;
    let tb = final_state.total_busts;
    let hidden = final_state.hidden;

    let init = reconstruct_init(rounds, th, tb, hv, hidden);
    let mut vm = VM::new(init);
    vm.run(final_state.mask, final_state.ops);
    let key = vm.key(hv, init);
    let dec = decrypt(&key);
    let (ok, _hf) = validate(&dec);

    if ok {
        println!("\n[+] FOUND FLAG sequence!");
        println!("waa rbahatoo: {}", String::from_utf8_lossy(&dec));
        FOUND.store(true, Ordering::SeqCst);
        exit(0);
    }
}

fn unpack(state: u32) -> Vec<u8> {
    let base = [
        0x11u8, 0x22, 0x33, 0x44, 0xAA,
        0x55, 0x66, 0x77, 0x88, 0x99,
        0xAB, 0xCD, 0xEF, 0x13, 0x37,
    ];
    let mut code = vec![0u8; base.len()];
    let mut prev: u8 = 0xC3;
    let mut t: u32 = 0xC0FFEE12;
    let mut st = state;

    for i in 0..base.len() {
        st ^= st.wrapping_mul(0x6D2B79F5);
        st ^= st.rotate_left(11).wrapping_add(t);
        t = t.wrapping_mul(0x45D9F3B) ^ st.rotate_right(i as u32 & 31);
        let key = ((st ^ t ^ (prev as u32)) >> ((i % 5) + 3)) as u8;
        let b = (base[i] as u32).wrapping_add(i as u32) as u8 ^ key ^ prev;
        prev = b.rotate_left((st % 7) as u32) ^ (t as u8);
        code[i] = b;
    }
    code
}

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
            shadow_state: state ^ 0x5555_AAAA,
            trace: 0,
            pc: 0,
            code: unpack(state),
            fingerprint: 0x1337_C0DE,
            last_op: 0,
            stall: 0,
            exec_noise: 0x5A,
        }
    }

    fn step(&mut self, hm: u64, ho: u64) {
        let mut op = self.code[self.pc % self.code.len()];
        op ^= (self.state & 0xFF) as u8;
        op ^= self.exec_noise;
        self.pc += 1;
        let effective_op = op ^ ((self.state & 0x07) as u8);

        if self.last_op == op {
            self.stall ^= self.trace;
            self.state ^= self.stall.rotate_left(3);
        }

        let eop = effective_op & 0xFF;
        match eop {
            0x11 => self.regs[0] ^= self.regs[1],
            0x22 => self.regs[1] = self.regs[1].wrapping_add(3),
            0x33 => self.regs[2] ^= 0x1337,
            0x44 => self.regs[3] = self.regs[3].wrapping_mul(3),
            0x55 => self.regs[4] = self.regs[4].rotate_left(1),
            0x66 => {
                if ((self.trace.wrapping_add(self.stall)) & 3) == 0 {
                    self.regs[5] ^= self.trace ^ self.state;
                } else {
                    self.regs[5] ^= self.trace.rotate_left(1);
                }
            }
            0x77 => self.regs[6] = self.regs[6].wrapping_add(self.state),
            0x88 => self.regs[7] ^= self.regs[0],
            0xAA => {
                if (self.trace & 1) == 0 {
                    self.regs[0] ^= 0xDEAD_BEEF;
                }
            }
            _ => { self.shadow_state = self.shadow_state.wrapping_add(eop as u32); }
        }

        self.last_op = op;

        if self.pc % 7 == 0 {
            let mut h_step = hm ^ ho.wrapping_mul(0x1337BEEF);
            h_step ^= h_step >> 33;
            h_step = h_step.wrapping_mul(0xFF51AFD7ED558CCD);
            h_step ^= h_step >> 33;
            h_step = h_step.wrapping_mul(0xC4CEB9FE1A85EC53);
            h_step ^= h_step >> 33;
            self.state ^= (h_step & 0xFFFFFFFF) as u32;
        }

        let jitter = (self.state ^ self.trace) & 3;
        if jitter == 0 {
            self.state ^= (self.trace ^ self.state ^ 0xDEAD_BEEF) & 0xFFFF;
        }

        self.trace = self.trace.rotate_left(5) ^ (op as u32);
        self.shadow_state = self.shadow_state.rotate_right(1) ^ self.trace;
        let idx = (self.state as usize) % self.code.len();
        self.code[idx] ^= (op as u8).wrapping_add(self.trace as u8);
        self.state ^= self.trace;
        self.state = self.state.rotate_right(3);
        self.exec_noise = self.exec_noise.wrapping_mul(31) ^ (self.trace as u8);
        self.fingerprint ^= self.trace.rotate_left(self.pc as u32);
        self.fingerprint = self.fingerprint.wrapping_mul(0x45d9f3b);
    }

    fn run(&mut self, hm: u64, ho: u64) {
        let steps = 64 + (self.state & 31) as usize;
        for _ in 0..steps {
            self.step(hm, ho);
        }
    }

    fn key(&self, hv: u64, gs: u32) -> [u8; 32] {
        let mut h = Sha256::new();
        for r in &self.regs { h.update(r.to_le_bytes()); }
        h.update(self.state.to_le_bytes());
        h.update(self.shadow_state.to_le_bytes());
        h.update(self.trace.to_le_bytes());
        h.update(hv.to_le_bytes());
        h.update(gs.to_le_bytes());
        h.update(self.fingerprint.to_le_bytes());
        h.finalize().into()
    }
}

fn reconstruct_init(rounds: u64, hits: u64, busts: u64, hv: u64, hidden: u64) -> u32 {
    let mut h = Sha256::new();
    h.update(rounds.to_le_bytes());
    h.update(hits.to_le_bytes());
    h.update(busts.to_le_bytes());
    h.update(hv.to_le_bytes());
    h.update(hidden.to_le_bytes());
    let ib = h.finalize();
    let mut init = u32::from_le_bytes(ib[0..4].try_into().unwrap());
    init ^= init.rotate_left(11);
    init = init.wrapping_mul(0x9E3779B1);
    init ^= init >> 16;
    init = init.rotate_left((busts % 32) as u32);
    init
}

fn decrypt(key: &[u8; 32]) -> Vec<u8> {
    ENC.iter().enumerate().map(|(i, b)| b ^ key[i % 32]).collect()
}

fn validate(dec: &[u8]) -> (bool, u32) {
    if !dec.starts_with(b"NSC{") { return (false, 0); }
    let mut hf: u32 = 0;
    for &b in dec {
        hf = hf.wrapping_add(b as u32).rotate_left(7) ^ 0x55_AAAA_55;
    }
    (hf == 0x58A07EB2, hf)
}

fn main() {
    println!("SFAYGA CASINO SOLVER — BFS/DFS Rayon");
    println!("========================================\n");

    let rounds_to_search: Vec<u64> = (7..=25).collect();

    for rounds in rounds_to_search {
        println!("[*] Exploring {} rounds...", rounds);
        
        let state = GameState::new();
        let mut initial_round = state.clone();
        initial_round.deal_round(1);
        
        let mut round1_moves = Vec::new();
        {
            let mut s = initial_round.clone();
            s.stand();
            s.end_round(1);
            round1_moves.push(s);
        }
        {
            let mut h = initial_round.clone();
            while h.player <= 21 {
                h.draw_card(1);
                if h.player > 21 {
                    let mut b = h.clone();
                    b.bust();
                    b.end_round(1);
                    round1_moves.push(b);
                    break;
                } else {
                    let mut s = h.clone();
                    s.stand();
                    s.end_round(1);
                    round1_moves.push(s);
                }
            }
        }

        round1_moves.into_par_iter().for_each(|s| {
            explore(s, 2, rounds);
        });

        if FOUND.load(Ordering::SeqCst) {
            exit(0);
        }
    }
}