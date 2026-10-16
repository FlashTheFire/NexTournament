package com.nextournament.app.data.network

import com.nextournament.app.data.security.SessionManager
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.*
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.min
import kotlin.random.Random

@Serializable
data class SeatSocketEvent(
    @SerialName("event") val event: String, // "SEAT_LOCKED", "SEAT_RELEASED", "SEAT_BOOKED", "ROOM_REVEALED", "WALLET_UPDATED"
    @SerialName("tournament_id") val tournamentId: Long,
    @SerialName("slot_number") val slotNumber: Int? = null,
    @SerialName("user_id") val userId: Long? = null,
    @SerialName("in_game_name") val inGameName: String? = null,
    @SerialName("room_id") val roomId: String? = null,
    @SerialName("room_password") val roomPassword: String? = null
)

sealed interface WebSocketStatus {
    object Disconnected : WebSocketStatus
    object Connecting : WebSocketStatus
    object Connected : WebSocketStatus
    data class Error(val message: String) : WebSocketStatus
}

@Singleton
class TournamentWebSocketClient @Inject constructor(
    private val sessionManager: SessionManager,
    private val json: Json
) {
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(15, TimeUnit.SECONDS) // Official 15s ping/pong heartbeat
        .build()

    private var webSocket: WebSocket? = null
    private val coroutineScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    private val _connectionStatus = MutableStateFlow<WebSocketStatus>(WebSocketStatus.Disconnected)
    val connectionStatus: StateFlow<WebSocketStatus> = _connectionStatus.asStateFlow()

    private val _events = MutableSharedFlow<SeatSocketEvent>(replay = 1)
    val events: SharedFlow<SeatSocketEvent> = _events.asSharedFlow()

    private var currentTournamentId: Long? = null
    private var isManuallyClosed = false
    private var reconnectAttempts = 0

    fun connect(tournamentId: Long, wsBaseUrl: String = "ws://10.0.2.2:8000") {
        disconnect()
        isManuallyClosed = false
        currentTournamentId = tournamentId
        _connectionStatus.value = WebSocketStatus.Connecting

        val token = sessionManager.getAccessToken() ?: ""
        val url = "$wsBaseUrl/ws/tournaments/$tournamentId/seats?token=$token"
        val request = Request.Builder().url(url).build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                reconnectAttempts = 0
                _connectionStatus.value = WebSocketStatus.Connected
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val event = json.decodeFromString(SeatSocketEvent.serializer(), text)
                    coroutineScope.launch {
                        _events.emit(event)
                    }
                } catch (e: Exception) {
                    // Ignore malformed ping frames
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _connectionStatus.value = WebSocketStatus.Error(t.message ?: "Connection failure")
                if (!isManuallyClosed && currentTournamentId == tournamentId) {
                    // Exponential backoff with jitter: 1s to 30s
                    val baseDelay = min(30000L, (1000L * (1 shl min(reconnectAttempts, 5))))
                    val jitter = Random.nextLong(0, 1000L)
                    val backoffDelay = baseDelay + jitter
                    reconnectAttempts++

                    coroutineScope.launch {
                        delay(backoffDelay)
                        if (!isManuallyClosed && currentTournamentId == tournamentId) {
                            connect(tournamentId, wsBaseUrl)
                        }
                    }
                }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                _connectionStatus.value = WebSocketStatus.Disconnected
            }
        })
    }

    fun disconnect() {
        isManuallyClosed = true
        webSocket?.close(1000, "User left match view")
        webSocket = null
        currentTournamentId = null
        reconnectAttempts = 0
        _connectionStatus.value = WebSocketStatus.Disconnected
    }
}
