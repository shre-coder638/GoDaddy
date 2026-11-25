package com.rushhour;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import com.rushhour.slot.SlotBook;

@SpringBootApplication
public class RushHourApplication implements WebMvcConfigurer {

    public static void main(String[] args) {
        SpringApplication.run(RushHourApplication.class, args);
    }

    @Bean
    SlotBook slotBook(@Value("${slot.capacity}") int capacity, @Value("${slot.first}") String first,
                      @Value("${slot.last}") String last, @Value("${slot.step-minutes}") int step) {
        return new SlotBook(capacity, first, last, step);
    }

    /** Hackathon setting: let the React dev server call the API from any origin. Tighten for real use. */
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**").allowedOrigins("*").allowedMethods("GET", "POST", "PATCH", "OPTIONS");
    }
}
