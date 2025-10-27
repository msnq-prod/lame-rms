from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Type
from typing import List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

# Auto-generated on 2025-10-27T06:21:38.656851+00:00 from db/schema.php

class ActionsSchema(BaseModel):
    """Schema for table actions."""
    model_config = ConfigDict(from_attributes=True)
    actions_id: int | None = None
    actions_name: str
    actionsCategories_id: int
    actions_dependent: str | None = None
    actions_incompatible: str | None = None
class ActionsCategoriesSchema(BaseModel):
    """Schema for table actionsCategories."""
    model_config = ConfigDict(from_attributes=True)
    actionsCategories_id: int | None = None
    actionsCategories_name: str
    actionsCategories_order: int | None = None
class AssetCategoriesSchema(BaseModel):
    """Schema for table assetCategories."""
    model_config = ConfigDict(from_attributes=True)
    assetCategories_id: int | None = None
    assetCategories_name: str
    assetCategories_fontAwesome: str | None = None
    assetCategories_rank: int
    assetCategoriesGroups_id: int
    instances_id: int | None = None
    assetCategories_deleted: bool
class AssetCategoriesGroupsSchema(BaseModel):
    """Schema for table assetCategoriesGroups."""
    model_config = ConfigDict(from_attributes=True)
    assetCategoriesGroups_id: int | None = None
    assetCategoriesGroups_name: str
    assetCategoriesGroups_fontAwesome: str | None = None
    assetCategoriesGroups_order: int
class AssetGroupsSchema(BaseModel):
    """Schema for table assetGroups."""
    model_config = ConfigDict(from_attributes=True)
    assetGroups_id: int | None = None
    assetGroups_name: str
    assetGroups_description: str | None = None
    assetGroups_deleted: bool
    users_userid: int | None = None
    instances_id: int
class AssetTypesSchema(BaseModel):
    """Schema for table assetTypes."""
    model_config = ConfigDict(from_attributes=True)
    assetTypes_id: int | None = None
    assetTypes_name: str
    assetCategories_id: int
    manufacturers_id: int
    instances_id: int | None = None
    assetTypes_description: str | None = None
    assetTypes_productLink: str | None = None
    assetTypes_definableFields: str | None = None
    assetTypes_mass: Decimal | None = None
    assetTypes_inserted: datetime | None = None
    assetTypes_dayRate: int
    assetTypes_weekRate: int
    assetTypes_value: int
class AssetsSchema(BaseModel):
    """Schema for table assets."""
    model_config = ConfigDict(from_attributes=True)
    assets_id: int | None = None
    assets_tag: str | None = None
    assetTypes_id: int
    assets_notes: str | None = None
    instances_id: int
    asset_definableFields_1: str | None = None
    asset_definableFields_2: str | None = None
    asset_definableFields_3: str | None = None
    asset_definableFields_4: str | None = None
    asset_definableFields_5: str | None = None
    asset_definableFields_6: str | None = None
    asset_definableFields_7: str | None = None
    asset_definableFields_8: str | None = None
    asset_definableFields_9: str | None = None
    asset_definableFields_10: str | None = None
    assets_inserted: datetime
    assets_dayRate: int | None = None
    assets_linkedTo: int | None = None
    assets_weekRate: int | None = None
    assets_value: int | None = None
    assets_mass: Decimal | None = None
    assets_deleted: bool
    assets_endDate: datetime | None = None
    assets_archived: str | None = None
    assets_assetGroups: str | None = None
    assets_storageLocation: int | None = None
    assets_showPublic: bool
class AssetsAssignmentsSchema(BaseModel):
    """Schema for table assetsAssignments."""
    model_config = ConfigDict(from_attributes=True)
    assetsAssignments_id: int | None = None
    assets_id: int
    projects_id: int
    assetsAssignments_comment: str | None = None
    assetsAssignments_customPrice: int
    assetsAssignments_discount: float
    assetsAssignments_timestamp: datetime | None = None
    assetsAssignments_deleted: bool
    assetsAssignmentsStatus_id: int | None = None
    assetsAssignments_linkedTo: int | None = None
class AssetsAssignmentsStatusSchema(BaseModel):
    """Schema for table assetsAssignmentsStatus."""
    model_config = ConfigDict(from_attributes=True)
    assetsAssignmentsStatus_id: int | None = None
    instances_id: int
    assetsAssignmentsStatus_name: str
    assetsAssignmentsStatus_order: int | None = None
class AssetsBarcodesSchema(BaseModel):
    """Schema for table assetsBarcodes."""
    model_config = ConfigDict(from_attributes=True)
    assetsBarcodes_id: int | None = None
    assets_id: int | None = None
    assetsBarcodes_value: str
    assetsBarcodes_type: str
    assetsBarcodes_notes: str | None = None
    assetsBarcodes_added: datetime
    users_userid: int | None = None
    assetsBarcodes_deleted: bool | None = None
class AssetsBarcodesScansSchema(BaseModel):
    """Schema for table assetsBarcodesScans."""
    model_config = ConfigDict(from_attributes=True)
    assetsBarcodesScans_id: int | None = None
    assetsBarcodes_id: int
    assetsBarcodesScans_timestamp: datetime
    users_userid: int | None = None
    locationsBarcodes_id: int | None = None
    location_assets_id: int | None = None
    assetsBarcodes_customLocation: str | None = None
class AuditLogSchema(BaseModel):
    """Schema for table auditLog."""
    model_config = ConfigDict(from_attributes=True)
    auditLog_id: int | None = None
    auditLog_actionType: str | None = None
    auditLog_actionTable: str | None = None
    auditLog_actionData: str | None = None
    auditLog_timestamp: datetime
    users_userid: int | None = None
    auditLog_actionUserid: int | None = None
    projects_id: int | None = None
    auditLog_deleted: bool
    auditLog_targetID: int | None = None
class AuthTokensSchema(BaseModel):
    """Schema for table authTokens."""
    model_config = ConfigDict(from_attributes=True)
    authTokens_id: int | None = None
    authTokens_token: str
    authTokens_created: datetime
    authTokens_ipAddress: str | None = None
    users_userid: int
    authTokens_valid: bool
    authTokens_adminId: int | None = None
    authTokens_deviceType: str
class ClientsSchema(BaseModel):
    """Schema for table clients."""
    model_config = ConfigDict(from_attributes=True)
    clients_id: int | None = None
    clients_name: str
    instances_id: int
    clients_deleted: bool
    clients_website: str | None = None
    clients_email: str | None = None
    clients_notes: str | None = None
    clients_address: str | None = None
    clients_phone: str | None = None
class CmsPagesSchema(BaseModel):
    """Schema for table cmsPages."""
    model_config = ConfigDict(from_attributes=True)
    cmsPages_id: int | None = None
    instances_id: int
    cmsPages_showNav: bool
    cmsPages_showPublic: bool
    cmsPages_showPublicNav: bool
    cmsPages_visibleToGroups: str | None = None
    cmsPages_navOrder: int
    cmsPages_fontAwesome: str | None = None
    cmsPages_name: str
    cmsPages_description: str | None = None
    cmsPages_archived: bool
    cmsPages_deleted: bool
    cmsPages_added: datetime
    cmsPages_subOf: int | None = None
class CmsPagesDraftsSchema(BaseModel):
    """Schema for table cmsPagesDrafts."""
    model_config = ConfigDict(from_attributes=True)
    cmsPagesDrafts_id: int | None = None
    cmsPages_id: int
    users_userid: int | None = None
    cmsPagesDrafts_timestamp: datetime
    cmsPagesDrafts_data: dict[str, Any] | list[Any] | None = None
    cmsPagesDrafts_changelog: str | None = None
    cmsPagesDrafts_revisionID: int
class CmsPagesViewsSchema(BaseModel):
    """Schema for table cmsPagesViews."""
    model_config = ConfigDict(from_attributes=True)
    cmsPagesViews_id: int | None = None
    cmsPages_id: int
    cmsPagesViews_timestamp: datetime
    users_userid: int | None = None
    cmsPages_type: bool
class CrewAssignmentsSchema(BaseModel):
    """Schema for table crewAssignments."""
    model_config = ConfigDict(from_attributes=True)
    crewAssignments_id: int | None = None
    users_userid: int | None = None
    projects_id: int
    crewAssignments_personName: str | None = None
    crewAssignments_role: str
    crewAssignments_comment: str | None = None
    crewAssignments_deleted: bool | None = None
    crewAssignments_rank: int | None = None
class EmailSentSchema(BaseModel):
    """Schema for table emailSent."""
    model_config = ConfigDict(from_attributes=True)
    emailSent_id: int | None = None
    users_userid: int
    emailSent_html: str
    emailSent_subject: str
    emailSent_sent: datetime
    emailSent_fromEmail: str
    emailSent_fromName: str
    emailSent_toName: str
    emailSent_toEmail: str
class EmailVerificationCodesSchema(BaseModel):
    """Schema for table emailVerificationCodes."""
    model_config = ConfigDict(from_attributes=True)
    emailVerificationCodes_id: int | None = None
    emailVerificationCodes_code: str
    emailVerificationCodes_used: bool
    emailVerificationCodes_timestamp: datetime
    emailVerificationCodes_valid: int
    users_userid: int
class InstanceActionsSchema(BaseModel):
    """Schema for table instanceActions."""
    model_config = ConfigDict(from_attributes=True)
    instanceActions_id: int | None = None
    instanceActions_name: str
    instanceActionsCategories_id: int
    instanceActions_dependent: str | None = None
    instanceActions_incompatible: str | None = None
class InstanceActionsCategoriesSchema(BaseModel):
    """Schema for table instanceActionsCategories."""
    model_config = ConfigDict(from_attributes=True)
    instanceActionsCategories_id: int | None = None
    instanceActionsCategories_name: str
    instanceActionsCategories_order: int
class InstancePositionsSchema(BaseModel):
    """Schema for table instancePositions."""
    model_config = ConfigDict(from_attributes=True)
    instancePositions_id: int | None = None
    instances_id: int
    instancePositions_displayName: str
    instancePositions_rank: int
    instancePositions_actions: str | None = None
    instancePositions_deleted: bool
class InstancesSchema(BaseModel):
    """Schema for table instances."""
    model_config = ConfigDict(from_attributes=True)
    instances_id: int | None = None
    instances_name: str
    instances_deleted: bool | None = None
    instances_plan: str | None = None
    instances_address: str | None = None
    instances_phone: str | None = None
    instances_email: str | None = None
    instances_website: str | None = None
    instances_weekStartDates: str | None = None
    instances_logo: int | None = None
    instances_emailHeader: int | None = None
    instances_termsAndPayment: str | None = None
    instances_storageLimit: int
    instances_config_linkedDefaultDiscount: float | None = None
    instances_config_currency: str
    instances_cableColours: str | None = None
    instances_publicConfig: str | None = None
class LocationsSchema(BaseModel):
    """Schema for table locations."""
    model_config = ConfigDict(from_attributes=True)
    locations_id: int | None = None
    locations_name: str
    clients_id: int | None = None
    instances_id: int
    locations_address: str | None = None
    locations_deleted: bool
    locations_subOf: int | None = None
    locations_notes: str | None = None
class LocationsBarcodesSchema(BaseModel):
    """Schema for table locationsBarcodes."""
    model_config = ConfigDict(from_attributes=True)
    locationsBarcodes_id: int | None = None
    locations_id: int
    locationsBarcodes_value: str
    locationsBarcodes_type: str
    locationsBarcodes_notes: str | None = None
    locationsBarcodes_added: datetime
    users_userid: int | None = None
    locationsBarcodes_deleted: bool | None = None
class LoginAttemptsSchema(BaseModel):
    """Schema for table loginAttempts."""
    model_config = ConfigDict(from_attributes=True)
    loginAttempts_id: int | None = None
    loginAttempts_timestamp: datetime
    loginAttempts_textEntered: str
    loginAttempts_ip: str | None = None
    loginAttempts_blocked: bool
    loginAttempts_successful: bool
class MaintenanceJobsSchema(BaseModel):
    """Schema for table maintenanceJobs."""
    model_config = ConfigDict(from_attributes=True)
    maintenanceJobs_id: int | None = None
    maintenanceJobs_assets: str
    maintenanceJobs_timestamp_added: datetime
    maintenanceJobs_timestamp_due: datetime | None = None
    maintenanceJobs_user_tagged: str | None = None
    maintenanceJobs_user_creator: int
    maintenanceJobs_user_assignedTo: int | None = None
    maintenanceJobs_title: str | None = None
    maintenanceJobs_faultDescription: str | None = None
    maintenanceJobs_priority: int
    instances_id: int
    maintenanceJobs_deleted: bool
    maintenanceJobsStatuses_id: int | None = None
    maintenanceJobs_flagAssets: bool
    maintenanceJobs_blockAssets: bool
class MaintenanceJobsMessagesSchema(BaseModel):
    """Schema for table maintenanceJobsMessages."""
    model_config = ConfigDict(from_attributes=True)
    maintenanceJobsMessages_id: int | None = None
    maintenanceJobs_id: int | None = None
    maintenanceJobsMessages_timestamp: datetime
    users_userid: int
    maintenanceJobsMessages_deleted: bool
    maintenanceJobsMessages_text: str | None = None
    maintenanceJobsMessages_file: int | None = None
class MaintenanceJobsStatusesSchema(BaseModel):
    """Schema for table maintenanceJobsStatuses."""
    model_config = ConfigDict(from_attributes=True)
    maintenanceJobsStatuses_id: int | None = None
    instances_id: int | None = None
    maintenanceJobsStatuses_name: str
    maintenanceJobsStatuses_order: bool
    maintenanceJobsStatuses_deleted: bool
    maintenanceJobsStatuses_showJobInMainList: bool
class ManufacturersSchema(BaseModel):
    """Schema for table manufacturers."""
    model_config = ConfigDict(from_attributes=True)
    manufacturers_id: int | None = None
    manufacturers_name: str
    instances_id: int | None = None
    manufacturers_internalAdamRMSNote: str | None = None
    manufacturers_website: str | None = None
    manufacturers_notes: str | None = None
class ModulesSchema(BaseModel):
    """Schema for table modules."""
    model_config = ConfigDict(from_attributes=True)
    modules_id: int | None = None
    instances_id: int
    users_userid: int
    modules_name: str
    modules_description: str | None = None
    modules_learningObjectives: str | None = None
    modules_deleted: bool
    modules_show: bool
    modules_thumbnail: int | None = None
    modules_type: bool
class ModulesStepsSchema(BaseModel):
    """Schema for table modulesSteps."""
    model_config = ConfigDict(from_attributes=True)
    modulesSteps_id: int | None = None
    modules_id: int
    modulesSteps_deleted: bool
    modulesSteps_show: bool
    modulesSteps_name: str
    modulesSteps_type: bool
    modulesSteps_content: str | None = None
    modulesSteps_completionTime: int | None = None
    modulesSteps_internalNotes: str | None = None
    modulesSteps_order: int
    modulesSteps_locked: bool
class PasswordResetCodesSchema(BaseModel):
    """Schema for table passwordResetCodes."""
    model_config = ConfigDict(from_attributes=True)
    passwordResetCodes_id: int | None = None
    passwordResetCodes_code: str
    passwordResetCodes_used: bool
    passwordResetCodes_timestamp: datetime
    passwordResetCodes_valid: int
    users_userid: int
class PaymentsSchema(BaseModel):
    """Schema for table payments."""
    model_config = ConfigDict(from_attributes=True)
    payments_id: int | None = None
    payments_amount: int
    payments_quantity: int
    payments_type: bool
    payments_reference: str | None = None
    payments_date: datetime
    payments_supplier: str | None = None
    payments_method: str | None = None
    payments_comment: str | None = None
    projects_id: int
    payments_deleted: bool
class PhinxlogSchema(BaseModel):
    """Schema for table phinxlog."""
    model_config = ConfigDict(from_attributes=True)
    version: int | None = None
    migration_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    breakpoint: bool
class PositionsSchema(BaseModel):
    """Schema for table positions."""
    model_config = ConfigDict(from_attributes=True)
    positions_id: int | None = None
    positions_displayName: str
    positions_positionsGroups: str | None = None
    positions_rank: int
class PositionsGroupsSchema(BaseModel):
    """Schema for table positionsGroups."""
    model_config = ConfigDict(from_attributes=True)
    positionsGroups_id: int | None = None
    positionsGroups_name: str
    positionsGroups_actions: str | None = None
class ProjectsSchema(BaseModel):
    """Schema for table projects."""
    model_config = ConfigDict(from_attributes=True)
    projects_id: int | None = None
    projects_name: str
    instances_id: int
    projects_manager: int
    projects_description: str | None = None
    projects_created: datetime
    clients_id: int | None = None
    projects_deleted: bool
    projects_archived: bool
    projects_dates_use_start: datetime | None = None
    projects_dates_use_end: datetime | None = None
    projects_dates_deliver_start: datetime | None = None
    projects_dates_deliver_end: datetime | None = None
    projects_status: int
    locations_id: int | None = None
    projects_invoiceNotes: str | None = None
    projects_defaultDiscount: float
    projectsTypes_id: int
class ProjectsFinanceCacheSchema(BaseModel):
    """Schema for table projectsFinanceCache."""
    model_config = ConfigDict(from_attributes=True)
    projectsFinanceCache_id: int | None = None
    projects_id: int
    projectsFinanceCache_timestamp: datetime
    projectsFinanceCache_timestampUpdated: datetime | None = None
    projectsFinanceCache_equipmentSubTotal: int | None = None
    projectsFinanceCache_equiptmentDiscounts: int | None = None
    projectsFinanceCache_equiptmentTotal: int | None = None
    projectsFinanceCache_salesTotal: int | None = None
    projectsFinanceCache_staffTotal: int | None = None
    projectsFinanceCache_externalHiresTotal: int | None = None
    projectsFinanceCache_paymentsReceived: int | None = None
    projectsFinanceCache_grandTotal: int | None = None
    projectsFinanceCache_value: int | None = None
    projectsFinanceCache_mass: Decimal | None = None
class ProjectsNotesSchema(BaseModel):
    """Schema for table projectsNotes."""
    model_config = ConfigDict(from_attributes=True)
    projectsNotes_id: int | None = None
    projectsNotes_title: str
    projectsNotes_text: str | None = None
    projectsNotes_userid: int
    projects_id: int
    projectsNotes_deleted: bool
class ProjectsTypesSchema(BaseModel):
    """Schema for table projectsTypes."""
    model_config = ConfigDict(from_attributes=True)
    projectsTypes_id: int | None = None
    projectsTypes_name: str
    instances_id: int
    projectsTypes_deleted: bool
    projectsTypes_config_finance: bool
    projectsTypes_config_files: int
    projectsTypes_config_assets: int
    projectsTypes_config_client: int
    projectsTypes_config_venue: int
    projectsTypes_config_notes: int
    projectsTypes_config_crew: int
class ProjectsVacantRolesSchema(BaseModel):
    """Schema for table projectsVacantRoles."""
    model_config = ConfigDict(from_attributes=True)
    projectsVacantRoles_id: int | None = None
    projects_id: int
    projectsVacantRoles_name: str
    projectsVacantRoles_description: str | None = None
    projectsVacantRoles_personSpecification: str | None = None
    projectsVacantRoles_deleted: bool
    projectsVacantRoles_open: bool
    projectsVacantRoles_showPublic: bool
    projectsVacantRoles_added: datetime
    projectsVacantRoles_deadline: datetime | None = None
    projectsVacantRoles_firstComeFirstServed: bool
    projectsVacantRoles_fileUploads: bool
    projectsVacantRoles_slots: int
    projectsVacantRoles_slotsFilled: int
    projectsVacantRoles_questions: dict[str, Any] | list[Any] | None = None
    projectsVacantRoles_collectPhone: bool
    projectsVacantRoles_privateToPM: bool
class ProjectsVacantRolesApplicationsSchema(BaseModel):
    """Schema for table projectsVacantRolesApplications."""
    model_config = ConfigDict(from_attributes=True)
    projectsVacantRolesApplications_id: int | None = None
    projectsVacantRoles_id: int
    users_userid: int
    projectsVacantRolesApplications_files: str | None = None
    projectsVacantRolesApplications_phone: str | None = None
    projectsVacantRolesApplications_applicantComment: str | None = None
    projectsVacantRolesApplications_deleted: bool
    projectsVacantRolesApplications_withdrawn: bool
    projectsVacantRolesApplications_submitted: datetime
    projectsVacantRolesApplications_questionAnswers: dict[str, Any] | list[Any] | None = None
    projectsVacantRolesApplications_status: bool
class S3filesSchema(BaseModel):
    """Schema for table s3files."""
    model_config = ConfigDict(from_attributes=True)
    s3files_id: int | None = None
    instances_id: int
    s3files_path: str | None = None
    s3files_name: str | None = None
    s3files_filename: str
    s3files_extension: str
    s3files_original_name: str | None = None
    s3files_region: str
    s3files_endpoint: str
    s3files_cdn_endpoint: str | None = None
    s3files_bucket: str
    s3files_meta_size: int
    s3files_meta_public: bool
    s3files_meta_type: int
    s3files_meta_subType: int | None = None
    s3files_meta_uploaded: datetime
    users_userid: int | None = None
    s3files_meta_deleteOn: datetime | None = None
    s3files_meta_physicallyStored: bool
    s3files_compressed: bool
class SignupCodesSchema(BaseModel):
    """Schema for table signupCodes."""
    model_config = ConfigDict(from_attributes=True)
    signupCodes_id: int | None = None
    signupCodes_name: str
    instances_id: int
    signupCodes_deleted: bool
    signupCodes_valid: bool
    signupCodes_notes: str | None = None
    signupCodes_role: str
    instancePositions_id: int | None = None
class UserInstancesSchema(BaseModel):
    """Schema for table userInstances."""
    model_config = ConfigDict(from_attributes=True)
    userInstances_id: int | None = None
    users_userid: int
    instancePositions_id: int
    userInstances_extraPermissions: str | None = None
    userInstances_label: str | None = None
    userInstances_deleted: bool
    signupCodes_id: int | None = None
    userInstances_archived: datetime | None = None
class UserModulesSchema(BaseModel):
    """Schema for table userModules."""
    model_config = ConfigDict(from_attributes=True)
    userModules_id: int | None = None
    modules_id: int
    users_userid: int
    userModules_stepsCompleted: str | None = None
    userModules_currentStep: int | None = None
    userModules_started: datetime
    userModules_updated: datetime
class UserModulesCertificationsSchema(BaseModel):
    """Schema for table userModulesCertifications."""
    model_config = ConfigDict(from_attributes=True)
    userModulesCertifications_id: int | None = None
    modules_id: int
    users_userid: int
    userModulesCertifications_revoked: bool
    userModulesCertifications_approvedBy: int
    userModulesCertifications_approvedComment: str | None = None
    userModulesCertifications_timestamp: datetime
class UserPositionsSchema(BaseModel):
    """Schema for table userPositions."""
    model_config = ConfigDict(from_attributes=True)
    userPositions_id: int | None = None
    users_userid: int | None = None
    userPositions_start: datetime
    userPositions_end: datetime | None = None
    positions_id: int | None = None
    userPositions_displayName: str | None = None
    userPositions_extraPermissions: str | None = None
    userPositions_show: bool
class UsersSchema(BaseModel):
    """Schema for table users."""
    model_config = ConfigDict(from_attributes=True)
    users_username: str | None = None
    users_name1: str | None = None
    users_name2: str | None = None
    users_userid: int | None = None
    users_salty1: str | None = None
    users_password: str | None = None
    users_salty2: str | None = None
    users_hash: str
    users_email: str | None = None
    users_created: datetime | None = None
    users_notes: str | None = None
    users_thumbnail: int | None = None
    users_changepass: bool
    users_selectedProjectID: int | None = None
    users_selectedInstanceIDLast: int | None = None
    users_suspended: bool
    users_deleted: bool | None = None
    users_emailVerified: bool
    users_social_facebook: str | None = None
    users_social_twitter: str | None = None
    users_social_instagram: str | None = None
    users_social_linkedin: str | None = None
    users_social_snapchat: str | None = None
    users_calendarHash: str | None = None
    users_widgets: str | None = None
    users_notificationSettings: str | None = None
    users_assetGroupsWatching: str | None = None

SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {
    "actions": ActionsSchema,
    "actionsCategories": ActionsCategoriesSchema,
    "assetCategories": AssetCategoriesSchema,
    "assetCategoriesGroups": AssetCategoriesGroupsSchema,
    "assetGroups": AssetGroupsSchema,
    "assetTypes": AssetTypesSchema,
    "assets": AssetsSchema,
    "assetsAssignments": AssetsAssignmentsSchema,
    "assetsAssignmentsStatus": AssetsAssignmentsStatusSchema,
    "assetsBarcodes": AssetsBarcodesSchema,
    "assetsBarcodesScans": AssetsBarcodesScansSchema,
    "auditLog": AuditLogSchema,
    "authTokens": AuthTokensSchema,
    "clients": ClientsSchema,
    "cmsPages": CmsPagesSchema,
    "cmsPagesDrafts": CmsPagesDraftsSchema,
    "cmsPagesViews": CmsPagesViewsSchema,
    "crewAssignments": CrewAssignmentsSchema,
    "emailSent": EmailSentSchema,
    "emailVerificationCodes": EmailVerificationCodesSchema,
    "instanceActions": InstanceActionsSchema,
    "instanceActionsCategories": InstanceActionsCategoriesSchema,
    "instancePositions": InstancePositionsSchema,
    "instances": InstancesSchema,
    "locations": LocationsSchema,
    "locationsBarcodes": LocationsBarcodesSchema,
    "loginAttempts": LoginAttemptsSchema,
    "maintenanceJobs": MaintenanceJobsSchema,
    "maintenanceJobsMessages": MaintenanceJobsMessagesSchema,
    "maintenanceJobsStatuses": MaintenanceJobsStatusesSchema,
    "manufacturers": ManufacturersSchema,
    "modules": ModulesSchema,
    "modulesSteps": ModulesStepsSchema,
    "passwordResetCodes": PasswordResetCodesSchema,
    "payments": PaymentsSchema,
    "phinxlog": PhinxlogSchema,
    "positions": PositionsSchema,
    "positionsGroups": PositionsGroupsSchema,
    "projects": ProjectsSchema,
    "projectsFinanceCache": ProjectsFinanceCacheSchema,
    "projectsNotes": ProjectsNotesSchema,
    "projectsTypes": ProjectsTypesSchema,
    "projectsVacantRoles": ProjectsVacantRolesSchema,
    "projectsVacantRolesApplications": ProjectsVacantRolesApplicationsSchema,
    "s3files": S3filesSchema,
    "signupCodes": SignupCodesSchema,
    "userInstances": UserInstancesSchema,
    "userModules": UserModulesSchema,
    "userModulesCertifications": UserModulesCertificationsSchema,
    "userPositions": UserPositionsSchema,
    "users": UsersSchema,
}

__all__ = [
    "ActionsSchema",
    "ActionsCategoriesSchema",
    "AssetCategoriesSchema",
    "AssetCategoriesGroupsSchema",
    "AssetGroupsSchema",
    "AssetTypesSchema",
    "AssetsSchema",
    "AssetsAssignmentsSchema",
    "AssetsAssignmentsStatusSchema",
    "AssetsBarcodesSchema",
    "AssetsBarcodesScansSchema",
    "AuditLogSchema",
    "AuthTokensSchema",
    "ClientsSchema",
    "CmsPagesSchema",
    "CmsPagesDraftsSchema",
    "CmsPagesViewsSchema",
    "CrewAssignmentsSchema",
    "EmailSentSchema",
    "EmailVerificationCodesSchema",
    "InstanceActionsSchema",
    "InstanceActionsCategoriesSchema",
    "InstancePositionsSchema",
    "InstancesSchema",
    "LocationsSchema",
    "LocationsBarcodesSchema",
    "LoginAttemptsSchema",
    "MaintenanceJobsSchema",
    "MaintenanceJobsMessagesSchema",
    "MaintenanceJobsStatusesSchema",
    "ManufacturersSchema",
    "ModulesSchema",
    "ModulesStepsSchema",
    "PasswordResetCodesSchema",
    "PaymentsSchema",
    "PhinxlogSchema",
    "PositionsSchema",
    "PositionsGroupsSchema",
    "ProjectsSchema",
    "ProjectsFinanceCacheSchema",
    "ProjectsNotesSchema",
    "ProjectsTypesSchema",
    "ProjectsVacantRolesSchema",
    "ProjectsVacantRolesApplicationsSchema",
    "S3filesSchema",
    "SignupCodesSchema",
    "UserInstancesSchema",
    "UserModulesSchema",
    "UserModulesCertificationsSchema",
    "UserPositionsSchema",
    "UsersSchema",
    "SCHEMA_REGISTRY",
]

