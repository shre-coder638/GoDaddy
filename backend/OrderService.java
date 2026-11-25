package com.rushhour.order;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import com.rushhour.menu.MenuService;
import com.rushhour.queue.QueueMeter;
import com.rushhour.slot.SlotBook;

/** In-memory orders. Every method is synchronized so the slot gate stays correct under a rush of requests. */
@Service
public class OrderService {

    public record PlaceResult(boolean accepted, Order order, String reason, String nextSlot) {}

    private final MenuService menu;
    private final SlotBook slots;
    private final int counters, baseSeconds, perLineSeconds;
    private final Map<Long, Order> orders = new LinkedHashMap<>();
    private final Map<String, Long> byKey = new HashMap<>();
    private long seq = 1000;

    public OrderService(MenuService menu, SlotBook slots, @Value("${queue.counters:1}") int counters,
                        @Value("${queue.service-base-seconds:6}") int baseSeconds,
                        @Value("${queue.service-per-line-seconds:5}") int perLineSeconds) {
        this.menu = menu;
        this.slots = slots;
        this.counters = counters;
        this.baseSeconds = baseSeconds;
        this.perLineSeconds = perLineSeconds;
    }

    public synchronized PlaceResult place(Dto.OrderRequest req, String idempotencyKey) {
        if (idempotencyKey != null && byKey.containsKey(idempotencyKey)) {      // same tap twice -> same order
            return new PlaceResult(true, orders.get(byKey.get(idempotencyKey)), null, null);
        }
        int total = 0;
        for (Dto.OrderLine line : req.items()) {
            var item = menu.find(line.itemId())
                    .orElseThrow(() -> new IllegalArgumentException("Unknown item_id: " + line.itemId()));
            total += item.price() * line.quantity();
        }
        SlotBook.Result r = slots.tryBook(req.pickupSlot());
        if ("invalid_slot".equals(r.reason())) throw new IllegalArgumentException("Invalid pickup_slot: " + req.pickupSlot());
        if (!r.accepted()) return new PlaceResult(false, null, r.reason(), r.nextSlot());
        Order order = new Order(++seq, req.student(), req.pickupSlot(), List.copyOf(req.items()), total,
                OrderStatus.PLACED, LocalDateTime.now());
        orders.put(order.id(), order);
        if (idempotencyKey != null) byKey.put(idempotencyKey, order.id());
        return new PlaceResult(true, order, null, null);
    }

    public synchronized List<Order> list(OrderStatus status, String slot) {
        return orders.values().stream()
                .filter(o -> status == null || o.status() == status)
                .filter(o -> slot == null || o.pickupSlot().equals(slot))
                .sorted((a, b) -> a.pickupSlot().equals(b.pickupSlot()) ? Long.compare(a.id(), b.id())
                        : a.pickupSlot().compareTo(b.pickupSlot()))
                .toList();
    }

    public synchronized Order setStatus(long id, OrderStatus next) {
        Order o = orders.get(id);
        if (o == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Order not found");
        if (o.status() == OrderStatus.CANCELLED || o.status() == OrderStatus.COLLECTED) {
            throw new IllegalStateException("Order is already " + o.status());
        }
        if (next == OrderStatus.CANCELLED) slots.release(o.pickupSlot());       // free the slot place
        Order updated = o.withStatus(next);
        orders.put(id, updated);
        return updated;
    }

    /** Kitchen screen: what to cook next, from orders still open (PLACED or PREPARING). */
    public synchronized List<Dto.CookItem> cookNext() {
        Map<String, Integer> totals = new HashMap<>();
        for (Order o : orders.values()) {
            if (!isOpen(o)) continue;
            for (Dto.OrderLine l : o.items()) totals.merge(menu.find(l.itemId()).get().name(), l.quantity(), Integer::sum);
        }
        return totals.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .map(e -> new Dto.CookItem(e.getKey(), e.getValue())).toList();
    }

    public synchronized Dto.QueueView queueMeter() {
        int open = 0, lines = 0;
        for (Order o : orders.values()) {
            if (isOpen(o)) { open++; lines += o.items().size(); }
        }
        return new Dto.QueueView(open, lines, QueueMeter.waitMinutes(open, lines, counters, baseSeconds, perLineSeconds));
    }

    public synchronized void reset() {
        orders.clear();
        byKey.clear();
        seq = 1000;
        slots.reset();
    }

    private static boolean isOpen(Order o) {
        return o.status() == OrderStatus.PLACED || o.status() == OrderStatus.PREPARING;
    }
}
