package com.rushhour.menu;

import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Optional;

import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

/** Menu comes from data/menu.json (same file as the data pack). */
@Service
public class MenuService {
    private final List<MenuItem> items;

    public MenuService(ObjectMapper mapper) throws IOException {
        try (InputStream in = new ClassPathResource("data/menu.json").getInputStream()) {
            items = mapper.readValue(in, new TypeReference<List<MenuItem>>() {});
        }
    }

    public List<MenuItem> all() { return items; }

    public Optional<MenuItem> find(String id) {
        return items.stream().filter(i -> i.id().equals(id)).findFirst();
    }
}
