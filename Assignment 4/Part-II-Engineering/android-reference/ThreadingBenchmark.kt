package com.example.assignment4

import android.os.Debug
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import java.util.concurrent.Executors
import kotlin.math.sqrt

data class BenchmarkResult(
    val strategy: String,
    val elapsedMs: Long,
    val threadCpuMs: Long,
    val checksum: Long,
    val workerCount: Int
)

/**
 * Call mainThreadBaseline() only from a test screen and with a bounded workload:
 * it deliberately blocks the UI thread so jank can be measured.
 * Call executorVersion() from the same screen; render results on the main thread.
 */
object ThreadingBenchmark {
    private fun calculateChunk(seed: Int, iterations: Int): Long {
        var value = seed.toLong()
        repeat(iterations) { i ->
            value = (value * 1664525L + 1013904223L + i) and 0xffffffffL
            // Keep the operation deterministic and non-trivial.
            if (i % 4096 == 0) value = (value xor sqrt((value and 0xffff).toDouble()).toLong())
        }
        return value
    }

    fun mainThreadBaseline(chunks: Int = 4, iterationsPerChunk: Int = 350_000): BenchmarkResult {
        val wallStart = SystemClock.elapsedRealtimeNanos()
        val cpuStart = Debug.threadCpuTimeNanos()
        var checksum = 0L
        repeat(chunks) { index -> checksum += calculateChunk(index, iterationsPerChunk) }
        return BenchmarkResult(
            "A_MAIN_THREAD",
            (SystemClock.elapsedRealtimeNanos() - wallStart) / 1_000_000,
            (Debug.threadCpuTimeNanos() - cpuStart) / 1_000_000,
            checksum,
            1
        )
    }

    fun executorVersion(
        chunks: Int = 4,
        iterationsPerChunk: Int = 350_000,
        workers: Int = 4,
        onComplete: (BenchmarkResult) -> Unit
    ) {
        val executor = Executors.newFixedThreadPool(workers)
        val wallStart = SystemClock.elapsedRealtimeNanos()
        val futures = (0 until chunks).map { index ->
            executor.submit<Long> { calculateChunk(index, iterationsPerChunk) }
        }
        Thread {
            val checksum = futures.sumOf { it.get() }
            val elapsed = (SystemClock.elapsedRealtimeNanos() - wallStart) / 1_000_000
            executor.shutdown()
            Handler(Looper.getMainLooper()).post {\n                onComplete(BenchmarkResult("B_EXECUTOR", elapsed, -1, checksum, workers))\n            }
        }.start()
    }
}
