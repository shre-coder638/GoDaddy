package com.rushhour.slot;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

import com.rushhour.queue.QueueMeter;

class SlotBookTest {

    private SlotBook book() { return new SlotBook(60, "09:30", "16:15", 15); }

    @Test
    void gateRefusesTheSixtyFirstOrderAndOffersNextSlot() {
        SlotBook b = book();
        for (int i = 0; i < 60; i++) assertTrue(b.tryBook("13:00").accepted());
        SlotBook.Result r = b.tryBook("13:00");
        assertFalse(r.accepted());
        assertEquals("slot_full", r.reason());
        assertEquals("13:15", r.nextSlot());
    }

    @Test
    void nextSlotSkipsFullSlots() {
        SlotBook b = book();
        for (int i = 0; i < 120; i++) b.tryBook(i < 60 ? "13:00" : "13:15");
        assertEquals("13:30", b.tryBook("13:00").nextSlot());
    }

    @Test
    void invalidSlotAndDayFull() {
        SlotBook b = new SlotBook(1, "16:00", "16:15", 15);
        assertEquals("invalid_slot", b.tryBook("13:07").reason());
        b.tryBook("16:00"); b.tryBook("16:15");
        SlotBook.Result r = b.tryBook("16:00");
        assertEquals("day_full", r.reason());
        assertNull(r.nextSlot());
    }

    @Test
    void releaseFreesAPlace() {
        SlotBook b = new SlotBook(1, "13:00", "13:15", 15);
        b.tryBook("13:00");
        assertFalse(b.tryBook("13:00").accepted());
        b.release("13:00");
        assertTrue(b.tryBook("13:00").accepted());
    }

    @Test
    void queueMeterMatchesDataPack() {
        assertEquals(5.6, QueueMeter.waitMinutes(24, 38, 1, 6, 5));
        assertEquals(2.8, QueueMeter.waitMinutes(24, 38, 2, 6, 5));
    }
}
