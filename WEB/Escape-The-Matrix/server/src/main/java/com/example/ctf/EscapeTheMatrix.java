package com.example.ctf;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.util.HashMap;
import java.util.Map;

@SpringBootApplication
public class EscapeTheMatrix {

    public static void main(String[] args) {
        printWarningBanner();

        SpringApplication app = new SpringApplication(EscapeTheMatrix.class);

        Map<String, Object> props = new HashMap<>();

        // Silence everything by default
        props.put("logging.level.root", "WARN");
        props.put("logging.level.org.springframework", "WARN");

        // OPTIONAL: allow ONLY bean wiring logs (remove if you want total silence)
        props.put(
            "logging.level.org.springframework.beans.factory.support.DefaultListableBeanFactory",
            "DEBUG"
        );

        // Prevent Spring from printing startup info banners
        app.setLogStartupInfo(false);

        app.setDefaultProperties(props);
        app.run(args);
    }

    private static void printWarningBanner() {
        System.out.println("███████╗███████╗ ██████╗ █████╗ ██████╗ ███████╗\n" + //
                        "██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝\n" + //
                        "█████╗  ███████╗██║     ███████║██████╔╝█████╗  \n" + //
                        "██╔══╝  ╚════██║██║     ██╔══██║██╔═══╝ ██╔══╝  \n" + //
                        "███████╗███████║╚██████╗██║  ██║██║     ███████╗\n" + //
                        "╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚══════╝\n" + //
                        "████████╗██╗  ██╗███████╗                       \n" + //
                        "╚══██╔══╝██║  ██║██╔════╝                       \n" + //
                        "   ██║   ███████║█████╗                         \n" + //
                        "   ██║   ██╔══██║██╔══╝                         \n" + //
                        "   ██║   ██║  ██║███████╗                       \n" + //
                        "   ╚═╝   ╚═╝  ╚═╝╚══════╝                       \n" + //
                        "███╗   ███╗██╗  ██╗████████╗██████╗  ██╗██╗  ██╗\n" + //
                        "████╗ ████║██║  ██║╚══██╔══╝██╔══██╗███║╚██╗██╔╝\n" + //
                        "██╔████╔██║███████║   ██║   ██████╔╝╚██║ ╚███╔╝ \n" + //
                        "██║╚██╔╝██║╚════██║   ██║   ██╔══██╗ ██║ ██╔██╗ \n" + //
                        "██║ ╚═╝ ██║     ██║   ██║   ██║  ██║ ██║██╔╝ ██╗\n" + //
                        "╚═╝     ╚═╝     ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═╝╚═╝  ╚═╝\n" + //
                        "                                                ");
    }
}
