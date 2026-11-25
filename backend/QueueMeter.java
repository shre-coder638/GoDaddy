package com.rushhour.queue;

/** Live queue meter: same formula as queue_wait_minutes() in the data pack. */
public final class QueueMeter {
    private QueueMeter() {}

    public static double waitMinutes(int openOrders, int openLines, int counters, int baseSeconds, int perLineSeconds) {
        double minutes = (openOrders * baseSeconds + openLines * perLineSeconds) / 60.0 / counters;
        return Math.round(minutes * 10) / 10.0;
    }
}
