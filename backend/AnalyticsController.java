package com.rushhour.web;

import java.io.IOException;
import java.io.InputStream;
import java.time.LocalDate;
import java.time.format.TextStyle;
import java.util.Locale;

import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/** Serves the data analyst's results (data/cook_ahead.json and data/slot_load.json). */
@RestController
@RequestMapping("/api/analytics")
public class AnalyticsController {
    private final JsonNode cookAhead;
    private final JsonNode typicalLoad;

    public AnalyticsController(ObjectMapper mapper) throws IOException {
        cookAhead = read(mapper, "data/cook_ahead.json").get("cook_ahead");
        typicalLoad = read(mapper, "data/slot_load.json");
    }

    /** Average units per item in the 12:45-1:45 rush. Defaults to today's weekday. */
    @GetMapping("/cook-ahead")
    public JsonNode cookAhead(@RequestParam(required = false) String day) {
        String d = day != null ? day : LocalDate.now().getDayOfWeek().getDisplayName(TextStyle.FULL, Locale.ENGLISH);
        JsonNode n = cookAhead.get(d);
        if (n == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "No data for " + d + " (canteen is open Mon-Sat)");
        return n;
    }

    /** Typical demand per slot from 30 days of data (100 = full counter capacity). */
    @GetMapping("/typical-load")
    public JsonNode typicalLoad() { return typicalLoad; }

    private static JsonNode read(ObjectMapper mapper, String path) throws IOException {
        try (InputStream in = new ClassPathResource(path).getInputStream()) {
            return mapper.readTree(in);
        }
    }
}
