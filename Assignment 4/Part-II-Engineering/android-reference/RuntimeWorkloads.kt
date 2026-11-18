package com.example.assignment4

import android.os.Debug
import android.os.SystemClock

object RuntimeWorkloads {
    fun cpuBound(iterations: Int): Long {
        var x = 0x1234abcdL
        repeat(iterations) { i -> x = (x * 1103515245L + 12345L + i) and 0x7fffffffL }
        return x
    }

    /** Allocates short-lived objects to exercise ART heap/GC. */
    fun allocationHeavy(count: Int): Long {
        data class Sample(val id: Int, val label: String, val values: IntArray)
        var checksum = 0L
        repeat(count) { i ->
            val sample = Sample(i, "row-$i", IntArray(16) { it + i })
            checksum += sample.values[i % 16]
        }
        return checksum
    }

    /** UI benchmark data; render with RecyclerView/Compose LazyColumn, not a giant ScrollView. */
    fun listRows(count: Int): List<String> =
        List(count) { index -> "Benchmark row $index — stable-id=$index" }

    fun measure(name: String, block: () -> Long): Map<String, Any> {
        val wallStart = SystemClock.elapsedRealtimeNanos()
        val cpuStart = Debug.threadCpuTimeNanos()
        val checksum = block()
        return mapOf(
            "workload" to name,
            "elapsed_ms" to (SystemClock.elapsedRealtimeNanos() - wallStart) / 1_000_000,
            "thread_cpu_ms" to (Debug.threadCpuTimeNanos() - cpuStart) / 1_000_000,
            "checksum" to checksum
        )
    }

    /** TEST ONLY: deliberately retains references to demonstrate a leak. */
    private val retainedActivities = mutableListOf<Any>()
    fun introduceLeakForTest(activity: Any) { retainedActivities.add(activity) }
    fun clearLeakAfterTest() { retainedActivities.clear() }

    /** TEST ONLY: call on main thread to create an ANR/jank demonstration. */
    fun blockCurrentThreadForTest(milliseconds: Long) {
        SystemClock.sleep(milliseconds)
    }
}
