package com.rushhour.order;

import java.time.LocalDateTime;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public record Order(long id, String student, @JsonProperty("pickup_slot") String pickupSlot, List<Dto.OrderLine> items,
                    int total, OrderStatus status, @JsonProperty("created_at") LocalDateTime createdAt) {

    public Order withStatus(OrderStatus next) {
        return new Order(id, student, pickupSlot, items, total, next, createdAt);
    }
}
