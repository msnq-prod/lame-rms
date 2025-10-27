from __future__ import annotations

from typing import Dict, Type

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, Numeric, String, Text
from sqlalchemy import BigInteger, SmallInteger

from app.db.base import Base

# Auto-generated on 2025-10-27T06:21:38.656851+00:00 from db/schema.php

class Actions(Base):
    __tablename__ = "actions"

    actions_id = Column(Integer, primary_key=True, autoincrement=True)
    actions_name = Column(String(255), nullable=False)
    actionsCategories_id = Column(Integer, ForeignKey("actionsCategories.actionsCategories_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    actions_dependent = Column(String(500))
    actions_incompatible = Column(String(500))

class ActionsCategories(Base):
    __tablename__ = "actionsCategories"

    actionsCategories_id = Column(Integer, primary_key=True, autoincrement=True)
    actionsCategories_name = Column(String(500), nullable=False)
    actionsCategories_order = Column(Integer)

class AssetCategories(Base):
    __tablename__ = "assetCategories"

    assetCategories_id = Column(Integer, primary_key=True, autoincrement=True)
    assetCategories_name = Column(String(200), nullable=False)
    assetCategories_fontAwesome = Column(String(100))
    assetCategories_rank = Column(Integer, nullable=False)
    assetCategoriesGroups_id = Column(Integer, ForeignKey("assetCategoriesGroups.assetCategoriesGroups_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"))
    assetCategories_deleted = Column(Boolean, nullable=False)

class AssetCategoriesGroups(Base):
    __tablename__ = "assetCategoriesGroups"

    assetCategoriesGroups_id = Column(Integer, primary_key=True, autoincrement=True)
    assetCategoriesGroups_name = Column(String(200), nullable=False)
    assetCategoriesGroups_fontAwesome = Column(String(300))
    assetCategoriesGroups_order = Column(Integer, nullable=False)

class AssetGroups(Base):
    __tablename__ = "assetGroups"

    assetGroups_id = Column(Integer, primary_key=True, autoincrement=True)
    assetGroups_name = Column(String(200), nullable=False)
    assetGroups_description = Column(Text)
    assetGroups_deleted = Column(Boolean, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"))
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

class AssetTypes(Base):
    __tablename__ = "assetTypes"

    assetTypes_id = Column(Integer, primary_key=True, autoincrement=True)
    assetTypes_name = Column(String(500), nullable=False)
    assetCategories_id = Column(Integer, ForeignKey("assetCategories.assetCategories_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    manufacturers_id = Column(Integer, ForeignKey("manufacturers.manufacturers_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"))
    assetTypes_description = Column(String(1000))
    assetTypes_productLink = Column(String(500))
    assetTypes_definableFields = Column(String(500))
    assetTypes_mass = Column(Numeric(55, 5))
    assetTypes_inserted = Column(DateTime)
    assetTypes_dayRate = Column(Integer, nullable=False)
    assetTypes_weekRate = Column(Integer, nullable=False)
    assetTypes_value = Column(Integer, nullable=False)

class Assets(Base):
    __tablename__ = "assets"

    assets_id = Column(Integer, primary_key=True, autoincrement=True)
    assets_tag = Column(String(200))
    assetTypes_id = Column(Integer, ForeignKey("assetTypes.assetTypes_id"), nullable=False)
    assets_notes = Column(Text)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    asset_definableFields_1 = Column(String(200))
    asset_definableFields_2 = Column(String(200))
    asset_definableFields_3 = Column(String(200))
    asset_definableFields_4 = Column(String(200))
    asset_definableFields_5 = Column(String(200))
    asset_definableFields_6 = Column(String(200))
    asset_definableFields_7 = Column(String(200))
    asset_definableFields_8 = Column(String(200))
    asset_definableFields_9 = Column(String(200))
    asset_definableFields_10 = Column(String(200))
    assets_inserted = Column(DateTime, nullable=False)
    assets_dayRate = Column(Integer)
    assets_linkedTo = Column(Integer, ForeignKey("assets.assets_id", ondelete="SET NULL", onupdate="SET NULL"))
    assets_weekRate = Column(Integer)
    assets_value = Column(Integer)
    assets_mass = Column(Numeric(55, 5))
    assets_deleted = Column(Boolean, nullable=False)
    assets_endDate = Column(DateTime)
    assets_archived = Column(String(200))
    assets_assetGroups = Column(String(500))
    assets_storageLocation = Column(Integer, ForeignKey("locations.locations_id", ondelete="SET NULL", onupdate="CASCADE"))
    assets_showPublic = Column(Boolean, nullable=False)

class AssetsAssignments(Base):
    __tablename__ = "assetsAssignments"

    assetsAssignments_id = Column(Integer, primary_key=True, autoincrement=True)
    assets_id = Column(Integer, ForeignKey("assets.assets_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projects_id = Column(Integer, ForeignKey("projects.projects_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    assetsAssignments_comment = Column(String(500))
    assetsAssignments_customPrice = Column(Integer, nullable=False)
    assetsAssignments_discount = Column(Float, nullable=False)
    assetsAssignments_timestamp = Column(DateTime)
    assetsAssignments_deleted = Column(Boolean, nullable=False)
    assetsAssignmentsStatus_id = Column(Integer)
    assetsAssignments_linkedTo = Column(Integer, ForeignKey("assetsAssignments.assetsAssignments_id", ondelete="CASCADE", onupdate="CASCADE"))

class AssetsAssignmentsStatus(Base):
    __tablename__ = "assetsAssignmentsStatus"

    assetsAssignmentsStatus_id = Column(Integer, primary_key=True, autoincrement=True)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    assetsAssignmentsStatus_name = Column(String(200), nullable=False)
    assetsAssignmentsStatus_order = Column(Integer)

class AssetsBarcodes(Base):
    __tablename__ = "assetsBarcodes"

    assetsBarcodes_id = Column(Integer, primary_key=True, autoincrement=True)
    assets_id = Column(Integer, ForeignKey("assets.assets_id", ondelete="CASCADE", onupdate="CASCADE"))
    assetsBarcodes_value = Column(String(500), nullable=False)
    assetsBarcodes_type = Column(String(500), nullable=False)
    assetsBarcodes_notes = Column(Text)
    assetsBarcodes_added = Column(DateTime, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="SET NULL", onupdate="CASCADE"))
    assetsBarcodes_deleted = Column(Boolean)

class AssetsBarcodesScans(Base):
    __tablename__ = "assetsBarcodesScans"

    assetsBarcodesScans_id = Column(Integer, primary_key=True, autoincrement=True)
    assetsBarcodes_id = Column(Integer, ForeignKey("assetsBarcodes.assetsBarcodes_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    assetsBarcodesScans_timestamp = Column(DateTime, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="SET NULL", onupdate="CASCADE"))
    locationsBarcodes_id = Column(Integer, ForeignKey("locationsBarcodes.locationsBarcodes_id", ondelete="CASCADE", onupdate="CASCADE"))
    location_assets_id = Column(Integer, ForeignKey("assets.assets_id", ondelete="SET NULL", onupdate="CASCADE"))
    assetsBarcodes_customLocation = Column(String(500))

class AuditLog(Base):
    __tablename__ = "auditLog"

    auditLog_id = Column(Integer, primary_key=True, autoincrement=True)
    auditLog_actionType = Column(String(500))
    auditLog_actionTable = Column(String(500))
    auditLog_actionData = Column(Text)
    auditLog_timestamp = Column(DateTime, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"))
    auditLog_actionUserid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"))
    projects_id = Column(Integer)
    auditLog_deleted = Column(Boolean, nullable=False)
    auditLog_targetID = Column(Integer)

class AuthTokens(Base):
    __tablename__ = "authTokens"

    authTokens_id = Column(Integer, primary_key=True, autoincrement=True)
    authTokens_token = Column(String(500), nullable=False)
    authTokens_created = Column(DateTime, nullable=False)
    authTokens_ipAddress = Column(String(500))
    users_userid = Column(Integer, ForeignKey("users.users_userid"), nullable=False)
    authTokens_valid = Column(Boolean, nullable=False)
    authTokens_adminId = Column(Integer, ForeignKey("users.users_userid"))
    authTokens_deviceType = Column(String(1000), nullable=False)

class Clients(Base):
    __tablename__ = "clients"

    clients_id = Column(Integer, primary_key=True, autoincrement=True)
    clients_name = Column(String(500), nullable=False)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    clients_deleted = Column(Boolean, nullable=False)
    clients_website = Column(String(500))
    clients_email = Column(String(500))
    clients_notes = Column(Text)
    clients_address = Column(String(500))
    clients_phone = Column(String(500))

class CmsPages(Base):
    __tablename__ = "cmsPages"

    cmsPages_id = Column(Integer, primary_key=True, autoincrement=True)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    cmsPages_showNav = Column(Boolean, nullable=False)
    cmsPages_showPublic = Column(Boolean, nullable=False)
    cmsPages_showPublicNav = Column(Boolean, nullable=False)
    cmsPages_visibleToGroups = Column(String(1000))
    cmsPages_navOrder = Column(Integer, nullable=False)
    cmsPages_fontAwesome = Column(String(500))
    cmsPages_name = Column(String(500), nullable=False)
    cmsPages_description = Column(Text)
    cmsPages_archived = Column(Boolean, nullable=False)
    cmsPages_deleted = Column(Boolean, nullable=False)
    cmsPages_added = Column(DateTime, nullable=False)
    cmsPages_subOf = Column(Integer, ForeignKey("cmsPages.cmsPages_id", ondelete="SET NULL", onupdate="CASCADE"))

class CmsPagesDrafts(Base):
    __tablename__ = "cmsPagesDrafts"

    cmsPagesDrafts_id = Column(Integer, primary_key=True, autoincrement=True)
    cmsPages_id = Column(Integer, ForeignKey("cmsPages.cmsPages_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="SET NULL", onupdate="CASCADE"))
    cmsPagesDrafts_timestamp = Column(DateTime, nullable=False)
    cmsPagesDrafts_data = Column(JSON)
    cmsPagesDrafts_changelog = Column(Text)
    cmsPagesDrafts_revisionID = Column(Integer, nullable=False)

class CmsPagesViews(Base):
    __tablename__ = "cmsPagesViews"

    cmsPagesViews_id = Column(Integer, primary_key=True, autoincrement=True)
    cmsPages_id = Column(Integer, ForeignKey("cmsPages.cmsPages_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    cmsPagesViews_timestamp = Column(DateTime, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="SET NULL", onupdate="CASCADE"))
    cmsPages_type = Column(Boolean, nullable=False)

class CrewAssignments(Base):
    __tablename__ = "crewAssignments"

    crewAssignments_id = Column(Integer, primary_key=True, autoincrement=True)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"))
    projects_id = Column(Integer, ForeignKey("projects.projects_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    crewAssignments_personName = Column(String(500))
    crewAssignments_role = Column(String(500), nullable=False)
    crewAssignments_comment = Column(String(500))
    crewAssignments_deleted = Column(Boolean)
    crewAssignments_rank = Column(Integer)

class EmailSent(Base):
    __tablename__ = "emailSent"

    emailSent_id = Column(Integer, primary_key=True, autoincrement=True)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    emailSent_html = Column(Text, nullable=False)
    emailSent_subject = Column(String(255), nullable=False)
    emailSent_sent = Column(DateTime, nullable=False)
    emailSent_fromEmail = Column(String(200), nullable=False)
    emailSent_fromName = Column(String(200), nullable=False)
    emailSent_toName = Column(String(200), nullable=False)
    emailSent_toEmail = Column(String(200), nullable=False)

class EmailVerificationCodes(Base):
    __tablename__ = "emailVerificationCodes"

    emailVerificationCodes_id = Column(Integer, primary_key=True, autoincrement=True)
    emailVerificationCodes_code = Column(String(1000), nullable=False)
    emailVerificationCodes_used = Column(Boolean, nullable=False)
    emailVerificationCodes_timestamp = Column(DateTime, nullable=False)
    emailVerificationCodes_valid = Column(Integer, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

class InstanceActions(Base):
    __tablename__ = "instanceActions"

    instanceActions_id = Column(Integer, primary_key=True, autoincrement=True)
    instanceActions_name = Column(String(255), nullable=False)
    instanceActionsCategories_id = Column(Integer, ForeignKey("instanceActionsCategories.instanceActionsCategories_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    instanceActions_dependent = Column(String(200))
    instanceActions_incompatible = Column(String(200))

class InstanceActionsCategories(Base):
    __tablename__ = "instanceActionsCategories"

    instanceActionsCategories_id = Column(Integer, primary_key=True, autoincrement=True)
    instanceActionsCategories_name = Column(String(255), nullable=False)
    instanceActionsCategories_order = Column(Integer, nullable=False)

class InstancePositions(Base):
    __tablename__ = "instancePositions"

    instancePositions_id = Column(Integer, primary_key=True, autoincrement=True)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    instancePositions_displayName = Column(String(500), nullable=False)
    instancePositions_rank = Column(Integer, nullable=False)
    instancePositions_actions = Column(String(5000))
    instancePositions_deleted = Column(Boolean, nullable=False)

class Instances(Base):
    __tablename__ = "instances"

    instances_id = Column(Integer, primary_key=True, autoincrement=True)
    instances_name = Column(String(200), nullable=False)
    instances_deleted = Column(Boolean)
    instances_plan = Column(String(500))
    instances_address = Column(String(1000))
    instances_phone = Column(String(200))
    instances_email = Column(String(200))
    instances_website = Column(String(200))
    instances_weekStartDates = Column(Text)
    instances_logo = Column(Integer)
    instances_emailHeader = Column(Integer)
    instances_termsAndPayment = Column(Text)
    instances_storageLimit = Column(BigInteger, nullable=False)
    instances_config_linkedDefaultDiscount = Column(Float)
    instances_config_currency = Column(String(200), nullable=False)
    instances_cableColours = Column(Text)
    instances_publicConfig = Column(Text)

class Locations(Base):
    __tablename__ = "locations"

    locations_id = Column(Integer, primary_key=True, autoincrement=True)
    locations_name = Column(String(500), nullable=False)
    clients_id = Column(Integer, ForeignKey("clients.clients_id", ondelete="SET NULL", onupdate="CASCADE"))
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    locations_address = Column(Text)
    locations_deleted = Column(Boolean, nullable=False)
    locations_subOf = Column(Integer, ForeignKey("locations.locations_id", ondelete="CASCADE", onupdate="CASCADE"))
    locations_notes = Column(Text)

class LocationsBarcodes(Base):
    __tablename__ = "locationsBarcodes"

    locationsBarcodes_id = Column(Integer, primary_key=True, autoincrement=True)
    locations_id = Column(Integer, nullable=False)
    locationsBarcodes_value = Column(String(500), nullable=False)
    locationsBarcodes_type = Column(String(500), nullable=False)
    locationsBarcodes_notes = Column(Text)
    locationsBarcodes_added = Column(DateTime, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="SET NULL", onupdate="CASCADE"))
    locationsBarcodes_deleted = Column(Boolean)

class LoginAttempts(Base):
    __tablename__ = "loginAttempts"

    loginAttempts_id = Column(Integer, primary_key=True, autoincrement=True)
    loginAttempts_timestamp = Column(DateTime, nullable=False)
    loginAttempts_textEntered = Column(String(500), nullable=False)
    loginAttempts_ip = Column(String(500))
    loginAttempts_blocked = Column(Boolean, nullable=False)
    loginAttempts_successful = Column(Boolean, nullable=False)

class MaintenanceJobs(Base):
    __tablename__ = "maintenanceJobs"

    maintenanceJobs_id = Column(Integer, primary_key=True, autoincrement=True)
    maintenanceJobs_assets = Column(String(500), nullable=False)
    maintenanceJobs_timestamp_added = Column(DateTime, nullable=False)
    maintenanceJobs_timestamp_due = Column(DateTime)
    maintenanceJobs_user_tagged = Column(String(500))
    maintenanceJobs_user_creator = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    maintenanceJobs_user_assignedTo = Column(Integer)
    maintenanceJobs_title = Column(String(500))
    maintenanceJobs_faultDescription = Column(String(500))
    maintenanceJobs_priority = Column(SmallInteger, nullable=False)
    instances_id = Column(Integer, nullable=False)
    maintenanceJobs_deleted = Column(Boolean, nullable=False)
    maintenanceJobsStatuses_id = Column(Integer)
    maintenanceJobs_flagAssets = Column(Boolean, nullable=False)
    maintenanceJobs_blockAssets = Column(Boolean, nullable=False)

class MaintenanceJobsMessages(Base):
    __tablename__ = "maintenanceJobsMessages"

    maintenanceJobsMessages_id = Column(Integer, primary_key=True, autoincrement=True)
    maintenanceJobs_id = Column(Integer, ForeignKey("maintenanceJobs.maintenanceJobs_id", ondelete="CASCADE", onupdate="CASCADE"))
    maintenanceJobsMessages_timestamp = Column(DateTime, nullable=False)
    users_userid = Column(Integer, nullable=False)
    maintenanceJobsMessages_deleted = Column(Boolean, nullable=False)
    maintenanceJobsMessages_text = Column(Text)
    maintenanceJobsMessages_file = Column(Integer, ForeignKey("s3files.s3files_id", ondelete="SET NULL", onupdate="CASCADE"))

class MaintenanceJobsStatuses(Base):
    __tablename__ = "maintenanceJobsStatuses"

    maintenanceJobsStatuses_id = Column(Integer, primary_key=True, autoincrement=True)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"))
    maintenanceJobsStatuses_name = Column(String(200), nullable=False)
    maintenanceJobsStatuses_order = Column(Boolean, nullable=False)
    maintenanceJobsStatuses_deleted = Column(Boolean, nullable=False)
    maintenanceJobsStatuses_showJobInMainList = Column(Boolean, nullable=False)

class Manufacturers(Base):
    __tablename__ = "manufacturers"

    manufacturers_id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturers_name = Column(String(500), nullable=False)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"))
    manufacturers_internalAdamRMSNote = Column(String(500))
    manufacturers_website = Column(String(200))
    manufacturers_notes = Column(Text)

class Modules(Base):
    __tablename__ = "modules"

    modules_id = Column(Integer, primary_key=True, autoincrement=True)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE"), nullable=False)
    modules_name = Column(String(500), nullable=False)
    modules_description = Column(Text)
    modules_learningObjectives = Column(Text)
    modules_deleted = Column(Boolean, nullable=False)
    modules_show = Column(Boolean, nullable=False)
    modules_thumbnail = Column(Integer, ForeignKey("s3files.s3files_id", ondelete="SET NULL", onupdate="CASCADE"))
    modules_type = Column(Boolean, nullable=False)

class ModulesSteps(Base):
    __tablename__ = "modulesSteps"

    modulesSteps_id = Column(Integer, primary_key=True, autoincrement=True)
    modules_id = Column(Integer, ForeignKey("modules.modules_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    modulesSteps_deleted = Column(Boolean, nullable=False)
    modulesSteps_show = Column(Boolean, nullable=False)
    modulesSteps_name = Column(String(500), nullable=False)
    modulesSteps_type = Column(Boolean, nullable=False)
    modulesSteps_content = Column(Text)
    modulesSteps_completionTime = Column(Integer)
    modulesSteps_internalNotes = Column(Text)
    modulesSteps_order = Column(Integer, nullable=False)
    modulesSteps_locked = Column(Boolean, nullable=False)

class PasswordResetCodes(Base):
    __tablename__ = "passwordResetCodes"

    passwordResetCodes_id = Column(Integer, primary_key=True, autoincrement=True)
    passwordResetCodes_code = Column(String(1000), nullable=False)
    passwordResetCodes_used = Column(Boolean, nullable=False)
    passwordResetCodes_timestamp = Column(DateTime, nullable=False)
    passwordResetCodes_valid = Column(Integer, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

class Payments(Base):
    __tablename__ = "payments"

    payments_id = Column(Integer, primary_key=True, autoincrement=True)
    payments_amount = Column(Integer, nullable=False)
    payments_quantity = Column(Integer, nullable=False)
    payments_type = Column(Boolean, nullable=False)
    payments_reference = Column(String(500))
    payments_date = Column(DateTime, nullable=False)
    payments_supplier = Column(String(500))
    payments_method = Column(String(500))
    payments_comment = Column(String(500))
    projects_id = Column(Integer, ForeignKey("projects.projects_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    payments_deleted = Column(Boolean, nullable=False)

class Phinxlog(Base):
    __tablename__ = "phinxlog"

    version = Column(BigInteger, primary_key=True)
    migration_name = Column(String(100))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    breakpoint = Column(Boolean, nullable=False)

class Positions(Base):
    __tablename__ = "positions"

    positions_id = Column(Integer, primary_key=True, autoincrement=True)
    positions_displayName = Column(String(255), nullable=False)
    positions_positionsGroups = Column(String(500))
    positions_rank = Column(SmallInteger, nullable=False)

class PositionsGroups(Base):
    __tablename__ = "positionsGroups"

    positionsGroups_id = Column(Integer, primary_key=True, autoincrement=True)
    positionsGroups_name = Column(String(255), nullable=False)
    positionsGroups_actions = Column(String(1000))

class Projects(Base):
    __tablename__ = "projects"

    projects_id = Column(Integer, primary_key=True, autoincrement=True)
    projects_name = Column(String(500), nullable=False)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projects_manager = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projects_description = Column(Text)
    projects_created = Column(DateTime, nullable=False)
    clients_id = Column(Integer, ForeignKey("clients.clients_id", ondelete="CASCADE", onupdate="CASCADE"))
    projects_deleted = Column(Boolean, nullable=False)
    projects_archived = Column(Boolean, nullable=False)
    projects_dates_use_start = Column(DateTime)
    projects_dates_use_end = Column(DateTime)
    projects_dates_deliver_start = Column(DateTime)
    projects_dates_deliver_end = Column(DateTime)
    projects_status = Column(SmallInteger, nullable=False)
    locations_id = Column(Integer, ForeignKey("locations.locations_id", ondelete="SET NULL", onupdate="CASCADE"))
    projects_invoiceNotes = Column(Text)
    projects_defaultDiscount = Column(Float, nullable=False)
    projectsTypes_id = Column(Integer, nullable=False)

class ProjectsFinanceCache(Base):
    __tablename__ = "projectsFinanceCache"

    projectsFinanceCache_id = Column(Integer, primary_key=True, autoincrement=True)
    projects_id = Column(Integer, ForeignKey("projects.projects_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projectsFinanceCache_timestamp = Column(DateTime, nullable=False)
    projectsFinanceCache_timestampUpdated = Column(DateTime)
    projectsFinanceCache_equipmentSubTotal = Column(Integer)
    projectsFinanceCache_equiptmentDiscounts = Column(Integer)
    projectsFinanceCache_equiptmentTotal = Column(Integer)
    projectsFinanceCache_salesTotal = Column(Integer)
    projectsFinanceCache_staffTotal = Column(Integer)
    projectsFinanceCache_externalHiresTotal = Column(Integer)
    projectsFinanceCache_paymentsReceived = Column(Integer)
    projectsFinanceCache_grandTotal = Column(Integer)
    projectsFinanceCache_value = Column(Integer)
    projectsFinanceCache_mass = Column(Numeric(55, 5))

class ProjectsNotes(Base):
    __tablename__ = "projectsNotes"

    projectsNotes_id = Column(Integer, primary_key=True, autoincrement=True)
    projectsNotes_title = Column(String(200), nullable=False)
    projectsNotes_text = Column(Text)
    projectsNotes_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projects_id = Column(Integer, ForeignKey("projects.projects_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projectsNotes_deleted = Column(Boolean, nullable=False)

class ProjectsTypes(Base):
    __tablename__ = "projectsTypes"

    projectsTypes_id = Column(Integer, primary_key=True, autoincrement=True)
    projectsTypes_name = Column(String(200), nullable=False)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projectsTypes_deleted = Column(Boolean, nullable=False)
    projectsTypes_config_finance = Column(Boolean, nullable=False)
    projectsTypes_config_files = Column(Integer, nullable=False)
    projectsTypes_config_assets = Column(Integer, nullable=False)
    projectsTypes_config_client = Column(Integer, nullable=False)
    projectsTypes_config_venue = Column(Integer, nullable=False)
    projectsTypes_config_notes = Column(Integer, nullable=False)
    projectsTypes_config_crew = Column(Integer, nullable=False)

class ProjectsVacantRoles(Base):
    __tablename__ = "projectsVacantRoles"

    projectsVacantRoles_id = Column(Integer, primary_key=True, autoincrement=True)
    projects_id = Column(Integer, ForeignKey("projects.projects_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projectsVacantRoles_name = Column(String(500), nullable=False)
    projectsVacantRoles_description = Column(Text)
    projectsVacantRoles_personSpecification = Column(Text)
    projectsVacantRoles_deleted = Column(Boolean, nullable=False)
    projectsVacantRoles_open = Column(Boolean, nullable=False)
    projectsVacantRoles_showPublic = Column(Boolean, nullable=False)
    projectsVacantRoles_added = Column(DateTime, nullable=False)
    projectsVacantRoles_deadline = Column(DateTime)
    projectsVacantRoles_firstComeFirstServed = Column(Boolean, nullable=False)
    projectsVacantRoles_fileUploads = Column(Boolean, nullable=False)
    projectsVacantRoles_slots = Column(Integer, nullable=False)
    projectsVacantRoles_slotsFilled = Column(Integer, nullable=False)
    projectsVacantRoles_questions = Column(JSON)
    projectsVacantRoles_collectPhone = Column(Boolean, nullable=False)
    projectsVacantRoles_privateToPM = Column(Boolean, nullable=False)

class ProjectsVacantRolesApplications(Base):
    __tablename__ = "projectsVacantRolesApplications"

    projectsVacantRolesApplications_id = Column(Integer, primary_key=True, autoincrement=True)
    projectsVacantRoles_id = Column(Integer, ForeignKey("projectsVacantRoles.projectsVacantRoles_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    projectsVacantRolesApplications_files = Column(Text)
    projectsVacantRolesApplications_phone = Column(String(255))
    projectsVacantRolesApplications_applicantComment = Column(Text)
    projectsVacantRolesApplications_deleted = Column(Boolean, nullable=False)
    projectsVacantRolesApplications_withdrawn = Column(Boolean, nullable=False)
    projectsVacantRolesApplications_submitted = Column(DateTime, nullable=False)
    projectsVacantRolesApplications_questionAnswers = Column(JSON)
    projectsVacantRolesApplications_status = Column(Boolean, nullable=False)

class S3files(Base):
    __tablename__ = "s3files"

    s3files_id = Column(Integer, primary_key=True, autoincrement=True)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    s3files_path = Column(String(255))
    s3files_name = Column(String(1000))
    s3files_filename = Column(String(255), nullable=False)
    s3files_extension = Column(String(255), nullable=False)
    s3files_original_name = Column(String(500))
    s3files_region = Column(String(255), nullable=False)
    s3files_endpoint = Column(String(255), nullable=False)
    s3files_cdn_endpoint = Column(String(255))
    s3files_bucket = Column(String(255), nullable=False)
    s3files_meta_size = Column(BigInteger, nullable=False)
    s3files_meta_public = Column(Boolean, nullable=False)
    s3files_meta_type = Column(SmallInteger, nullable=False)
    s3files_meta_subType = Column(Integer)
    s3files_meta_uploaded = Column(DateTime, nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="SET NULL", onupdate="CASCADE"))
    s3files_meta_deleteOn = Column(DateTime)
    s3files_meta_physicallyStored = Column(Boolean, nullable=False)
    s3files_compressed = Column(Boolean, nullable=False)

class SignupCodes(Base):
    __tablename__ = "signupCodes"

    signupCodes_id = Column(Integer, primary_key=True, autoincrement=True)
    signupCodes_name = Column(String(200), nullable=False)
    instances_id = Column(Integer, ForeignKey("instances.instances_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    signupCodes_deleted = Column(Boolean, nullable=False)
    signupCodes_valid = Column(Boolean, nullable=False)
    signupCodes_notes = Column(Text)
    signupCodes_role = Column(String(500), nullable=False)
    instancePositions_id = Column(Integer, ForeignKey("instancePositions.instancePositions_id", ondelete="SET NULL", onupdate="CASCADE"))

class UserInstances(Base):
    __tablename__ = "userInstances"

    userInstances_id = Column(Integer, primary_key=True, autoincrement=True)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    instancePositions_id = Column(Integer, ForeignKey("instancePositions.instancePositions_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    userInstances_extraPermissions = Column(String(5000))
    userInstances_label = Column(String(500))
    userInstances_deleted = Column(Boolean, nullable=False)
    signupCodes_id = Column(Integer, ForeignKey("signupCodes.signupCodes_id", ondelete="SET NULL", onupdate="CASCADE"))
    userInstances_archived = Column(DateTime)

class UserModules(Base):
    __tablename__ = "userModules"

    userModules_id = Column(Integer, primary_key=True, autoincrement=True)
    modules_id = Column(Integer, ForeignKey("modules.modules_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    userModules_stepsCompleted = Column(String(1000))
    userModules_currentStep = Column(Integer, ForeignKey("modulesSteps.modulesSteps_id", ondelete="SET NULL", onupdate="CASCADE"))
    userModules_started = Column(DateTime, nullable=False)
    userModules_updated = Column(DateTime, nullable=False)

class UserModulesCertifications(Base):
    __tablename__ = "userModulesCertifications"

    userModulesCertifications_id = Column(Integer, primary_key=True, autoincrement=True)
    modules_id = Column(Integer, ForeignKey("modules.modules_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    userModulesCertifications_revoked = Column(Boolean, nullable=False)
    userModulesCertifications_approvedBy = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    userModulesCertifications_approvedComment = Column(String(2000))
    userModulesCertifications_timestamp = Column(DateTime, nullable=False)

class UserPositions(Base):
    __tablename__ = "userPositions"

    userPositions_id = Column(Integer, primary_key=True, autoincrement=True)
    users_userid = Column(Integer, ForeignKey("users.users_userid", ondelete="CASCADE", onupdate="CASCADE"))
    userPositions_start = Column(DateTime, nullable=False)
    userPositions_end = Column(DateTime)
    positions_id = Column(Integer, ForeignKey("positions.positions_id", ondelete="CASCADE", onupdate="CASCADE"))
    userPositions_displayName = Column(String(255))
    userPositions_extraPermissions = Column(String(500))
    userPositions_show = Column(Boolean, nullable=False)

class Users(Base):
    __tablename__ = "users"

    users_username = Column(String(200))
    users_name1 = Column(String(100))
    users_name2 = Column(String(100))
    users_userid = Column(Integer, primary_key=True, autoincrement=True)
    users_salty1 = Column(String(30))
    users_password = Column(String(150))
    users_salty2 = Column(String(50))
    users_hash = Column(String(255), nullable=False)
    users_email = Column(String(257))
    users_created = Column(DateTime)
    users_notes = Column(Text)
    users_thumbnail = Column(Integer)
    users_changepass = Column(Boolean, nullable=False)
    users_selectedProjectID = Column(Integer)
    users_selectedInstanceIDLast = Column(Integer)
    users_suspended = Column(Boolean, nullable=False)
    users_deleted = Column(Boolean)
    users_emailVerified = Column(Boolean, nullable=False)
    users_social_facebook = Column(String(100))
    users_social_twitter = Column(String(100))
    users_social_instagram = Column(String(100))
    users_social_linkedin = Column(String(100))
    users_social_snapchat = Column(String(100))
    users_calendarHash = Column(String(200))
    users_widgets = Column(String(500))
    users_notificationSettings = Column(Text)
    users_assetGroupsWatching = Column(String(200))

MODEL_REGISTRY: Dict[str, Type[Base]] = {
    "actions": Actions,
    "actionsCategories": ActionsCategories,
    "assetCategories": AssetCategories,
    "assetCategoriesGroups": AssetCategoriesGroups,
    "assetGroups": AssetGroups,
    "assetTypes": AssetTypes,
    "assets": Assets,
    "assetsAssignments": AssetsAssignments,
    "assetsAssignmentsStatus": AssetsAssignmentsStatus,
    "assetsBarcodes": AssetsBarcodes,
    "assetsBarcodesScans": AssetsBarcodesScans,
    "auditLog": AuditLog,
    "authTokens": AuthTokens,
    "clients": Clients,
    "cmsPages": CmsPages,
    "cmsPagesDrafts": CmsPagesDrafts,
    "cmsPagesViews": CmsPagesViews,
    "crewAssignments": CrewAssignments,
    "emailSent": EmailSent,
    "emailVerificationCodes": EmailVerificationCodes,
    "instanceActions": InstanceActions,
    "instanceActionsCategories": InstanceActionsCategories,
    "instancePositions": InstancePositions,
    "instances": Instances,
    "locations": Locations,
    "locationsBarcodes": LocationsBarcodes,
    "loginAttempts": LoginAttempts,
    "maintenanceJobs": MaintenanceJobs,
    "maintenanceJobsMessages": MaintenanceJobsMessages,
    "maintenanceJobsStatuses": MaintenanceJobsStatuses,
    "manufacturers": Manufacturers,
    "modules": Modules,
    "modulesSteps": ModulesSteps,
    "passwordResetCodes": PasswordResetCodes,
    "payments": Payments,
    "phinxlog": Phinxlog,
    "positions": Positions,
    "positionsGroups": PositionsGroups,
    "projects": Projects,
    "projectsFinanceCache": ProjectsFinanceCache,
    "projectsNotes": ProjectsNotes,
    "projectsTypes": ProjectsTypes,
    "projectsVacantRoles": ProjectsVacantRoles,
    "projectsVacantRolesApplications": ProjectsVacantRolesApplications,
    "s3files": S3files,
    "signupCodes": SignupCodes,
    "userInstances": UserInstances,
    "userModules": UserModules,
    "userModulesCertifications": UserModulesCertifications,
    "userPositions": UserPositions,
    "users": Users,
}

__all__ = [
    "Actions",
    "ActionsCategories",
    "AssetCategories",
    "AssetCategoriesGroups",
    "AssetGroups",
    "AssetTypes",
    "Assets",
    "AssetsAssignments",
    "AssetsAssignmentsStatus",
    "AssetsBarcodes",
    "AssetsBarcodesScans",
    "AuditLog",
    "AuthTokens",
    "Clients",
    "CmsPages",
    "CmsPagesDrafts",
    "CmsPagesViews",
    "CrewAssignments",
    "EmailSent",
    "EmailVerificationCodes",
    "InstanceActions",
    "InstanceActionsCategories",
    "InstancePositions",
    "Instances",
    "Locations",
    "LocationsBarcodes",
    "LoginAttempts",
    "MaintenanceJobs",
    "MaintenanceJobsMessages",
    "MaintenanceJobsStatuses",
    "Manufacturers",
    "Modules",
    "ModulesSteps",
    "PasswordResetCodes",
    "Payments",
    "Phinxlog",
    "Positions",
    "PositionsGroups",
    "Projects",
    "ProjectsFinanceCache",
    "ProjectsNotes",
    "ProjectsTypes",
    "ProjectsVacantRoles",
    "ProjectsVacantRolesApplications",
    "S3files",
    "SignupCodes",
    "UserInstances",
    "UserModules",
    "UserModulesCertifications",
    "UserPositions",
    "Users",
    "MODEL_REGISTRY",
]

