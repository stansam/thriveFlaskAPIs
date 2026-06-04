import click
from flask import Flask
from app.core.cli.commands import (
    seed_user_command,
    seed_corporate_command,
    seed_client_command,
    seed_fee_command,
    seed_media_command,
    seed_package_command,
    seed_booking_command,
    seed_booking_passenger_command,
    seed_fee_snapshot_command,
    seed_payment_command,
    seed_referral_command,
    seed_loyalty_command,
    seed_notification_command,
    seed_notification_template_command,
    seed_audit_command,
    seed_user_preference_command,
    seed_client_preference_command,
    seed_notification_delivery_command,
    seed_car_booking_command,
    seed_flight_booking_command,
    seed_hotel_booking_command,
    seed_package_booking_command,
    seed_fee_schedule_command,
    seed_package_items_command,
    seed_package_media_command,
    seed_package_price_tier_command,
    seed_package_insurance_command,
    create_admin_command,
    routes_command,
    rotate_mfa_keys_command,
    manage_tables_command,
    seed_db_command,
)

@click.command("db-seed")
@click.pass_context
def db_seed_alias(ctx: click.Context) -> None:
    """Alias for seed-db."""
    ctx.invoke(seed_db_command)

def _register_cli_commands(app: Flask) -> None:
    """Attach modular Flask CLI commands."""
    # Seeding commands
    app.cli.add_command(seed_db_command)
    app.cli.add_command(db_seed_alias)  # legacy alias
    app.cli.add_command(seed_user_command)
    app.cli.add_command(seed_user_preference_command)
    app.cli.add_command(seed_corporate_command)
    app.cli.add_command(seed_client_command)
    app.cli.add_command(seed_client_preference_command)
    app.cli.add_command(seed_fee_schedule_command)
    app.cli.add_command(seed_fee_command)
    app.cli.add_command(seed_media_command)
    app.cli.add_command(seed_package_command)
    app.cli.add_command(seed_package_items_command)
    app.cli.add_command(seed_package_media_command)
    app.cli.add_command(seed_package_price_tier_command)
    app.cli.add_command(seed_package_insurance_command)
    app.cli.add_command(seed_booking_command)
    app.cli.add_command(seed_car_booking_command)
    app.cli.add_command(seed_flight_booking_command)
    app.cli.add_command(seed_hotel_booking_command)
    app.cli.add_command(seed_package_booking_command)
    app.cli.add_command(seed_booking_passenger_command)
    app.cli.add_command(seed_fee_snapshot_command)
    app.cli.add_command(seed_payment_command)
    app.cli.add_command(seed_referral_command)
    app.cli.add_command(seed_loyalty_command)
    app.cli.add_command(seed_notification_template_command)
    app.cli.add_command(seed_notification_command)
    app.cli.add_command(seed_notification_delivery_command)
    app.cli.add_command(seed_audit_command)

    # Core/Management commands
    app.cli.add_command(create_admin_command)
    app.cli.add_command(routes_command)
    app.cli.add_command(rotate_mfa_keys_command)
    app.cli.add_command(manage_tables_command)
