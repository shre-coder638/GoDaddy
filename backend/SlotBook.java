package com.rushhour.slot;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** The gate. Counts orders per 15-minute slot and refuses a full slot. Plain Java, thread-safe. */
public class SlotBook {

    public record Result(boolean accepted, String slot, String reason, String nextSlot) {}

    public record SlotLoad(String slot, int booked, int capacity, int fillPct, String status) {}

    private final int capacity;
    private final List<String> slots = new ArrayList<>();
    private final Map<String, Integer> booked = new LinkedHashMap<>();

    public SlotBook(int capacity, String first, String last, int stepMinutes) {
        this.capacity = capacity;
        for (int m = toMinutes(first); m <= toMinutes(last); m += stepMinutes) {
            slots.add(format(m));
            booked.put(format(m), 0);
        }
    }

    /** Accept if the slot has space; otherwise refuse and offer the next free slot. */
    public synchronized Result tryBook(String slot) {
        Integer count = booked.get(slot);
        if (count == null) return new Result(false, slot, "invalid_slot", null);
        if (count < capacity) {
            booked.put(slot, count + 1);
            return new Result(true, slot, null, null);
        }
        for (int j = slots.indexOf(slot) + 1; j < slots.size(); j++) {
            if (booked.get(slots.get(j)) < capacity) return new Result(false, slot, "slot_full", slots.get(j));
        }
        return new Result(false, slot, "day_full", null);
    }

    /** Give a place back (cancelled order). */
    public synchronized void release(String slot) {
        booked.computeIfPresent(slot, (k, v) -> Math.max(0, v - 1));
    }

    public synchronized void reset() {
        booked.replaceAll((k, v) -> 0);
    }

    public synchronized List<SlotLoad> loads() {
        List<SlotLoad> out = new ArrayList<>();
        for (String s : slots) {
            int b = booked.get(s);
            int pct = (int) Math.round(b * 100.0 / capacity);
            out.add(new SlotLoad(s, b, capacity, pct, pct >= 100 ? "full" : pct >= 70 ? "busy" : "quiet"));
        }
        return out;
    }

    /** Nudge: nearest slot (later first) that is under 70% full. Not the gate. */
    public synchronized Optional<String> suggest(String desired) {
        int i = slots.indexOf(desired);
        if (i < 0) return Optional.empty();
        for (int d = 0; d < slots.size(); d++) {
            for (int j : new int[] {i + d, i - d}) {
                if (j >= 0 && j < slots.size() && booked.get(slots.get(j)) < capacity * 0.7) return Optional.of(slots.get(j));
            }
        }
        return Optional.empty();
    }

    private static int toMinutes(String hhmm) {
        String[] p = hhmm.split(":");
        return Integer.parseInt(p[0]) * 60 + Integer.parseInt(p[1]);
    }

    private static String format(int minutes) {
        return String.format("%02d:%02d", minutes / 60, minutes % 60);
    }
}
