# app/interface/package/events.py
"""
Event subscribers for Package domain events.
"""
from __future__ import annotations

from app.core.events import subscribe
from app.core.events.dataclass.package import (
    PackageCreatedEvent,
    PackageUpdatedEvent,
    PackagePublishedEvent,
    PackagePausedEvent,
    PackageArchivedEvent,
    PackageDuplicatedEvent,
    PackageHighlightAddedEvent,
    PackageHighlightUpdatedEvent,
    PackageHighlightDeletedEvent,
    PackageInclusionAddedEvent,
    PackageInclusionUpdatedEvent,
    PackageInclusionDeletedEvent,
    PackageItineraryDayAddedEvent,
    PackageItineraryDayUpdatedEvent,
    PackageItineraryDayDeletedEvent,
    PackagePriceTierAddedEvent,
    PackagePriceTierUpdatedEvent,
    PackagePriceTierDeactivatedEvent,
    PackageMediaAttachedEvent,
    PackageMediaRemovedEvent,
    PackageInsuranceAddedEvent,
    PackageInsuranceUpdatedEvent,
    PackageInsuranceDeletedEvent,
)
from app.core.dependencies import get_services
from app.enums import NotificationEventType, RecipientType
from app.core.logging import get_logger

logger = get_logger(__name__)

@subscribe(PackageCreatedEvent)
def on_package_created(event: PackageCreatedEvent) -> None:
    logger.info("Package created: package_id=%s title=%s actor_id=%s", event.package_id, event.title, event.actor_id)

@subscribe(PackageUpdatedEvent)
def on_package_updated(event: PackageUpdatedEvent) -> None:
    logger.info("Package updated: package_id=%s actor_id=%s", event.package_id, event.actor_id)

@subscribe(PackagePublishedEvent)
def on_package_published(event: PackagePublishedEvent) -> None:
    logger.info("Package published: package_id=%s title=%s actor_id=%s", event.package_id, event.title, event.actor_id)
    services = get_services()
    if event.actor_id:
        try:
            services.notification.dispatch(
                event_type=NotificationEventType.PACKAGE_PUBLISHED,
                recipient_type=RecipientType.USER,
                recipient_id=event.actor_id,
                context={
                    "package_id": event.package_id,
                    "title": event.title,
                    "actor_id": event.actor_id,
                },
            )
        except Exception as exc:
            logger.error(
                "Failed to dispatch package published notification for package %s: %s",
                event.package_id,
                exc,
            )
            
    # Asynchronously dispatch PACKAGE_DEAL_ALERT to opted-in clients
    try:
        from app.repository import client_repo
        clients = client_repo.marketing_opt_in_list()
        for client in clients:
            services.notification.dispatch(
                event_type=NotificationEventType.PACKAGE_DEAL_ALERT,
                recipient_type=RecipientType.CLIENT,
                recipient_id=client.id,
                context={
                    "package_id": event.package_id,
                    "title": event.title,
                    "client_name": client.full_name,
                },
            )
    except Exception as exc:
        logger.error(
            "Failed to dispatch package deal alerts for package %s: %s",
            event.package_id,
            exc,
        )

@subscribe(PackagePausedEvent)
def on_package_paused(event: PackagePausedEvent) -> None:
    logger.warning("Package paused: package_id=%s actor_id=%s", event.package_id, event.actor_id)

@subscribe(PackageArchivedEvent)
def on_package_archived(event: PackageArchivedEvent) -> None:
    logger.warning("Package archived: package_id=%s actor_id=%s", event.package_id, event.actor_id)

@subscribe(PackageDuplicatedEvent)
def on_package_duplicated(event: PackageDuplicatedEvent) -> None:
    logger.info("Package duplicated: source_package_id=%s new_package_id=%s new_title=%s actor_id=%s",
                event.source_package_id, event.new_package_id, event.new_title, event.actor_id)

@subscribe(PackageHighlightAddedEvent)
def on_highlight_added(event: PackageHighlightAddedEvent) -> None:
    logger.debug("Highlight added: package_id=%s highlight_id=%s actor_id=%s", event.package_id, event.highlight_id, event.actor_id)

@subscribe(PackageHighlightUpdatedEvent)
def on_highlight_updated(event: PackageHighlightUpdatedEvent) -> None:
    logger.debug("Highlight updated: package_id=%s highlight_id=%s actor_id=%s", event.package_id, event.highlight_id, event.actor_id)

@subscribe(PackageHighlightDeletedEvent)
def on_highlight_deleted(event: PackageHighlightDeletedEvent) -> None:
    logger.debug("Highlight deleted: package_id=%s highlight_id=%s actor_id=%s", event.package_id, event.highlight_id, event.actor_id)

@subscribe(PackageInclusionAddedEvent)
def on_inclusion_added(event: PackageInclusionAddedEvent) -> None:
    logger.debug("Inclusion added: package_id=%s inclusion_id=%s actor_id=%s", event.package_id, event.inclusion_id, event.actor_id)

@subscribe(PackageInclusionUpdatedEvent)
def on_inclusion_updated(event: PackageInclusionUpdatedEvent) -> None:
    logger.debug("Inclusion updated: package_id=%s inclusion_id=%s actor_id=%s", event.package_id, event.inclusion_id, event.actor_id)

@subscribe(PackageInclusionDeletedEvent)
def on_inclusion_deleted(event: PackageInclusionDeletedEvent) -> None:
    logger.debug("Inclusion deleted: package_id=%s inclusion_id=%s actor_id=%s", event.package_id, event.inclusion_id, event.actor_id)

@subscribe(PackageItineraryDayAddedEvent)
def on_itinerary_day_added(event: PackageItineraryDayAddedEvent) -> None:
    logger.debug("Itinerary day added: package_id=%s day_id=%s actor_id=%s", event.package_id, event.day_id, event.actor_id)

@subscribe(PackageItineraryDayUpdatedEvent)
def on_itinerary_day_updated(event: PackageItineraryDayUpdatedEvent) -> None:
    logger.debug("Itinerary day updated: package_id=%s day_id=%s actor_id=%s", event.package_id, event.day_id, event.actor_id)

@subscribe(PackageItineraryDayDeletedEvent)
def on_itinerary_day_deleted(event: PackageItineraryDayDeletedEvent) -> None:
    logger.debug("Itinerary day deleted: package_id=%s day_id=%s actor_id=%s", event.package_id, event.day_id, event.actor_id)

@subscribe(PackagePriceTierAddedEvent)
def on_price_tier_added(event: PackagePriceTierAddedEvent) -> None:
    logger.debug("Price tier added: package_id=%s tier_id=%s actor_id=%s", event.package_id, event.tier_id, event.actor_id)

@subscribe(PackagePriceTierUpdatedEvent)
def on_price_tier_updated(event: PackagePriceTierUpdatedEvent) -> None:
    logger.debug("Price tier updated: package_id=%s tier_id=%s actor_id=%s", event.package_id, event.tier_id, event.actor_id)

@subscribe(PackagePriceTierDeactivatedEvent)
def on_price_tier_deactivated(event: PackagePriceTierDeactivatedEvent) -> None:
    logger.warning("Price tier deactivated: package_id=%s tier_id=%s actor_id=%s", event.package_id, event.tier_id, event.actor_id)

@subscribe(PackageMediaAttachedEvent)
def on_media_attached(event: PackageMediaAttachedEvent) -> None:
    logger.debug("Media attached: package_id=%s asset_id=%s media_id=%s is_cover=%s actor_id=%s",
                 event.package_id, event.asset_id, event.media_id, event.is_cover, event.actor_id)

@subscribe(PackageMediaRemovedEvent)
def on_media_removed(event: PackageMediaRemovedEvent) -> None:
    logger.debug("Media removed: package_id=%s media_id=%s actor_id=%s", event.package_id, event.media_id, event.actor_id)

@subscribe(PackageInsuranceAddedEvent)
def on_insurance_added(event: PackageInsuranceAddedEvent) -> None:
    logger.debug("Insurance added: package_id=%s insurance_id=%s actor_id=%s", event.package_id, event.insurance_id, event.actor_id)

@subscribe(PackageInsuranceUpdatedEvent)
def on_insurance_updated(event: PackageInsuranceUpdatedEvent) -> None:
    logger.debug("Insurance updated: package_id=%s insurance_id=%s actor_id=%s", event.package_id, event.insurance_id, event.actor_id)

@subscribe(PackageInsuranceDeletedEvent)
def on_insurance_deleted(event: PackageInsuranceDeletedEvent) -> None:
    logger.debug("Insurance deleted: package_id=%s insurance_id=%s actor_id=%s", event.package_id, event.insurance_id, event.actor_id)
