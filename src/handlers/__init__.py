"""
NexTournament v2.0 - Handler Routers Aggregator
Combines user-facing tournament discovery, movie-ticket seat selection,
inline queries, dual-wallet deposits, withdrawals, proofs, gamification, and admin suites.
"""

from aiogram import Router
from src.handlers.start import router as start_router
from src.handlers.tournament import router as tournament_router
from src.handlers.seat_picker import router as seat_picker_router
from src.handlers.inline_query import router as inline_query_router
from src.handlers.deposit import router as deposit_router
from src.handlers.deposit_crypto import router as deposit_crypto_router
from src.handlers.withdraw import router as withdraw_router
from src.handlers.proof_submission import router as proof_submission_router
from src.handlers.referral import router as referral_router
from src.handlers.daily_bonus import router as daily_bonus_router
from src.handlers.redeem import router as redeem_router
from src.handlers.leaderboard import router as leaderboard_router
from src.handlers.admin.create_match import router as admin_create_match_router
from src.handlers.admin.broadcast_credentials import router as admin_broadcast_router
from src.handlers.admin.results import router as admin_results_router
from src.handlers.admin.approvals import router as admin_approvals_router
from src.handlers.admin.panel import router as admin_panel_router


def get_handlers_router() -> Router:
    """Combines all user onboarding, booking, financial, gamification, and admin routers."""
    main_router = Router(name="main_handlers")
    # Onboarding & Core Navigation
    main_router.include_router(start_router)

    # Tournaments & Booking
    main_router.include_router(tournament_router)
    main_router.include_router(seat_picker_router)
    main_router.include_router(inline_query_router)

    # Financial & Wallets
    main_router.include_router(deposit_router)
    main_router.include_router(deposit_crypto_router)
    main_router.include_router(withdraw_router)

    # Proofs & Disputes
    main_router.include_router(proof_submission_router)

    # Gamification & Community
    main_router.include_router(referral_router)
    main_router.include_router(daily_bonus_router)
    main_router.include_router(redeem_router)
    main_router.include_router(leaderboard_router)

    # Admin Suites
    main_router.include_router(admin_panel_router)
    main_router.include_router(admin_create_match_router)
    main_router.include_router(admin_broadcast_router)
    main_router.include_router(admin_results_router)
    main_router.include_router(admin_approvals_router)
    return main_router
