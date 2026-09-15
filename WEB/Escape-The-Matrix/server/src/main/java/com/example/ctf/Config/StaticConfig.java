package com.example.ctf.Config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class StaticConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // Block direct access to server assets (GIF files for the CTF)
        // These should only be accessible via the MatrixController
        // The GIF files are in classpath:/assets/ but we block direct access
        registry.addResourceHandler("/assets/*.gif")
                .addResourceLocations("classpath:/non-existent-location/");
        
        // Allow Spring Boot's default static content serving
        // This will serve the frontend React app from /static/
        // Allow /assets/** for frontend JS/CSS but block direct GIF access
    }
}
