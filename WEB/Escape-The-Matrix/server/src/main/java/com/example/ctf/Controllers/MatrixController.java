package com.example.ctf.Controllers;

//log4j attack vector libs
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.FileCopyUtils;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpSession;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;
import java.util.List;

@RestController
@RequestMapping("/api")
public class MatrixController {

    private static final Logger logger = LogManager.getLogger(MatrixController.class);
    private static final String SESSION_TIME_KEY = "lastRequestTime";
    private static final long COOLDOWN_MS = 1000;

    // GIF sequence - need enough GIFs for all fragments (can repeat GIFs if needed)
    private static final List<String> GIF_SEQUENCE = Arrays.asList(
        "a9f3c2b7d1.gif",
        "0x7e4c91fa.gif",
        "m_4d8b2c9e.gif",
        "c8f1e0a3d6.gif",
        "vx_29af7c1e.gif",
        "7b0e4d9cfa.gif",
        "k3c9e7a1f0.gif",
        "n0d_84c7fa2e.gif",
        "e7f2c9a1d4.gif",
        "z_1c0a9e7fb.gif",
        "4f9e7c2a1d.gif",
        "q8a1c9f0e7.gif",
        "x0f7e1c9a2.gif"
    );

    
    private static final List<String> ID_FRAGMENTS_B64 = Arrays.asList(
        "UE9TVCAvYXB",
        "pL200dHIxeF",
        "9Fc2M0cDNk",
        "L2VuVDNyX3",
        "RoM192MGlE",
        "IENvbnRlbn",
        "QtVHlwZTog",
        "YXBwbGljYX",
        "Rpb24vanNv",
        "biB7InRyNG",
        "MzIjoiLi4i",
        "LCJ2MGlkIj",
        "oiLi4iLCIzbnRyMHB5IjoiLi4iLCJuMGRFIjoiLi4ifQ=="
    );


    // ==================================================================================
    // PUBLIC SAFE ENDPOINT - Used by the frontend to get GIFs and collect fragments
    // ==================================================================================
    @PostMapping("/escape")
    public ResponseEntity<byte[]> escape(@RequestBody EscapeRequestPayload payload, HttpSession session) {
        // Safe logging - no vulnerability here
        logger.info("Escape request from node: {}", payload.getNode());

        // Enforce cooldown (session-based but doesn't track progress)
        Long lastRequestTime = (Long) session.getAttribute(SESSION_TIME_KEY);
        long now = System.currentTimeMillis();
        if (lastRequestTime != null && (now - lastRequestTime) < COOLDOWN_MS) {
            return new ResponseEntity<>(HttpStatus.TOO_MANY_REQUESTS);
        }
        session.setAttribute(SESSION_TIME_KEY, now);

        // Get the step from the frontend payload
        Integer requestedStep = payload.getStep();
        if (requestedStep == null || requestedStep < 0 || requestedStep >= GIF_SEQUENCE.size()) {
            return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
        }

        try {
            // Determine filename and fragment for the requested step
            String filename = GIF_SEQUENCE.get(requestedStep);
            String fragment = ID_FRAGMENTS_B64.get(requestedStep);

            // Read GIF from classpath (inside the JAR at src/main/resources/assets)
            ClassPathResource resource = new ClassPathResource("assets/" + filename);
            if (!resource.exists()) {
                logger.error("GIF resource not found in classpath: assets/" + filename);
                return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
            }
            InputStream inputStream = resource.getInputStream();
            byte[] fileContent = FileCopyUtils.copyToByteArray(inputStream);

            // Return GIF with fragment in header
            return ResponseEntity.ok()
                    .contentType(MediaType.IMAGE_GIF)
                    .header("X-Matrix-Id", fragment)
                    .body(fileContent);

        } catch (IOException e) {
            logger.error("Error reading GIF file for step " + requestedStep, e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }


    // ==================================================================================
    // HIDDEN VULNERABLE ENDPOINT - The attack vector (Log4j RCE via v0id parameter)
    // This endpoint is intentionally hidden and should be discovered via fragments
    // ==================================================================================
    @PostMapping("/m4tr1x_Esc4p3d/enT3r_th3_v0iD")
    public ResponseEntity<String> enterTheVoid(@RequestBody VulnerableRequestPayload payload, HttpSession session) {
        // VULNERABLE LOGGING STATEMENT - v0id parameter is susceptible to Log4j RCE
        logger.error("Matrix void signal: {}", payload.getV0id());
        
        // Additional safe logging
        logger.info("Trace: {}, Entropy: {}, Node: {}", 
            payload.getTr4c3(), payload.get3ntr0py(), payload.getN0dE());

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_JSON)
                .body("{\"status\":\"void_entered\",\"message\":\"The matrix has been breached\"}");
    }


    // ==================================================================================
    // Request Payload Classes
    // ==================================================================================
    
    // Safe endpoint payload
    public static class EscapeRequestPayload {
        private Integer step;
        private String signal;
        private String trace;
        private String entropy;
        private String node;

        public Integer getStep() { return step; }
        public void setStep(Integer step) { this.step = step; }
        public String getSignal() { return signal; }
        public void setSignal(String signal) { this.signal = signal; }
        public String getTrace() { return trace; }
        public void setTrace(String trace) { this.trace = trace; }
        public String getEntropy() { return entropy; }
        public void setEntropy(String entropy) { this.entropy = entropy; }
        public String getNode() { return node; }
        public void setNode(String node) { this.node = node; }
    }

    // Vulnerable endpoint payload - uses obfuscated field names
    public static class VulnerableRequestPayload {
        private String tr4c3;
        private String v0id;      // THIS FIELD IS VULNERABLE TO LOG4J RCE
        private String _3ntr0py;
        private String n0dE;

        public String getTr4c3() { return tr4c3; }
        public void setTr4c3(String tr4c3) { this.tr4c3 = tr4c3; }
        public String getV0id() { return v0id; }
        public void setV0id(String v0id) { this.v0id = v0id; }
        public String get3ntr0py() { return _3ntr0py; }
        public void set3ntr0py(String _3ntr0py) { this._3ntr0py = _3ntr0py; }
        public String getN0dE() { return n0dE; }
        public void setN0dE(String n0dE) { this.n0dE = n0dE; }
    }
}
