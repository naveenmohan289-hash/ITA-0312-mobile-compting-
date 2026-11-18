package com.example.assignment4

enum class Motion { MOVING, STATIONARY }
enum class Network { WIFI, CELLULAR, NONE }
enum class PowerBand { NORMAL, CONSERVE, CRITICAL }

data class TrackingInput(
    val batteryPercent: Int,
    val network: Network,
    val motion: Motion,
    val charging: Boolean,
    val deviceHot: Boolean,
    val lowPowerMode: Boolean
)

data class TrackingDecision(
    val powerBand: PowerBand,
    val sampleIntervalSeconds: Int,
    val uploadAction: String,
    val encryptBeforeQueue: Boolean = true,
    val requireAuthenticatedTls: Boolean = true
)

/** Pure policy function: easy to unit-test with boundary and transition cases. */
object TrackingPowerPolicy {
    fun evaluate(input: TrackingInput): TrackingDecision {
        require(input.batteryPercent in 0..100)
        if (input.deviceHot || input.batteryPercent <= 10) {
            return TrackingDecision(PowerBand.CRITICAL, 300, "DEFER_EXCEPT_EMERGENCY")
        }
        if (input.lowPowerMode || input.batteryPercent <= 20) {
            return TrackingDecision(
                PowerBand.CONSERVE, 120,
                if (input.network == Network.NONE) "QUEUE" else "UPLOAD_WIFI_OR_CHARGING"
            )
        }
        if (input.motion == Motion.MOVING) {
            return TrackingDecision(
                PowerBand.NORMAL, 15,
                if (input.network == Network.NONE) "QUEUE" else "BATCH_UPLOAD"
            )
        }
        if (input.charging && input.network == Network.WIFI) {
            return TrackingDecision(PowerBand.NORMAL, 10, "UPLOAD_BATCH_NOW")
        }
        return TrackingDecision(
            PowerBand.NORMAL, 60,
            if (input.network == Network.NONE) "QUEUE" else "BATCH_UPLOAD"
        )
    }
}
