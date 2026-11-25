package com.rushhour.order;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

/** Request/response shapes. JSON uses snake_case to match gate_replay.json from the data pack. */
public final class Dto {
    private Dto() {}

    public record OrderLine(@NotBlank @JsonProperty("item_id") String itemId, @Min(1) @Max(10) int quantity) {}

    public record OrderRequest(@NotBlank String student, @NotBlank @JsonProperty("pickup_slot") String pickupSlot,
                               @NotEmpty @Valid List<OrderLine> items) {}

    public record Accepted(boolean accepted, Order order) {}

    public record Refusal(boolean accepted, String reason, @JsonProperty("next_slot") String nextSlot) {}

    public record SlotView(String slot, int booked, int capacity, @JsonProperty("fill_pct") int fillPct, String status) {}

    public record CookItem(String item, int qty) {}

    public record QueueView(@JsonProperty("open_orders") int openOrders, @JsonProperty("open_lines") int openLines,
                            @JsonProperty("wait_minutes") double waitMinutes) {}
}
