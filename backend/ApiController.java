package com.rushhour.web;

import java.util.List;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.rushhour.menu.MenuItem;
import com.rushhour.menu.MenuService;
import com.rushhour.order.Dto;
import com.rushhour.order.Order;
import com.rushhour.order.OrderService;
import com.rushhour.order.OrderStatus;
import com.rushhour.slot.SlotBook;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api")
public class ApiController {
    private final MenuService menu;
    private final SlotBook slots;
    private final OrderService orders;

    public ApiController(MenuService menu, SlotBook slots, OrderService orders) {
        this.menu = menu;
        this.slots = slots;
        this.orders = orders;
    }

    @GetMapping("/menu")
    public List<MenuItem> menu() { return menu.all(); }

    /** Live slot loads: students pick a quieter slot from this. */
    @GetMapping("/slots")
    public List<Dto.SlotView> slots() {
        return slots.loads().stream()
                .map(s -> new Dto.SlotView(s.slot(), s.booked(), s.capacity(), s.fillPct(), s.status())).toList();
    }

    @GetMapping("/slots/suggest")
    public Map<String, Object> suggest(@RequestParam String desired) {
        return slots.suggest(desired)
                .map(s -> Map.<String, Object>of("slot", s, "message",
                        s.equals(desired) ? "Slot available" : desired + " is busy. " + s + " is quieter - ready faster!"))
                .orElse(Map.<String, Object>of("slot", "", "message", "No quiet slot nearby"));
    }

    /** 201 = order placed with a pickup slot. 409 = slot full, with next_slot offered (the gate). */
    @PostMapping("/orders")
    public ResponseEntity<?> place(@Valid @RequestBody Dto.OrderRequest request,
                                   @RequestHeader(value = "Idempotency-Key", required = false) String key) {
        OrderService.PlaceResult r = orders.place(request, key);
        if (r.accepted()) return ResponseEntity.status(201).body(new Dto.Accepted(true, r.order()));
        return ResponseEntity.status(409).body(new Dto.Refusal(false, r.reason(), r.nextSlot()));
    }

    /** Kitchen list. Optional filters: ?status=PLACED&slot=13:00 */
    @GetMapping("/orders")
    public List<Order> list(@RequestParam(required = false) OrderStatus status,
                            @RequestParam(required = false) String slot) {
        return orders.list(status, slot);
    }

    @PatchMapping("/orders/{id}/status")
    public Order setStatus(@PathVariable long id, @RequestBody Map<String, String> body) {
        String status = body.get("status");
        if (status == null) throw new IllegalArgumentException("status is required");
        return orders.setStatus(id, OrderStatus.valueOf(status.toUpperCase()));
    }

    @GetMapping("/kitchen/cook-next")
    public List<Dto.CookItem> cookNext() { return orders.cookNext(); }

    @GetMapping("/queue/meter")
    public Dto.QueueView queueMeter() { return orders.queueMeter(); }

    /** Demo only: clear orders and slots so the gate test can be run again. */
    @PostMapping("/admin/reset")
    public Map<String, String> reset() {
        orders.reset();
        return Map.of("status", "reset");
    }
}
