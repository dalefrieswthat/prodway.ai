/**
 * FormPilot constants — single source of truth (Netflix: explicit config).
 * No magic strings in content/background.
 */
export const STORAGE_KEYS = {
  COMPANY_PROFILE: 'formpilot_company_profile',
  API_BASE_URL: 'formpilot_api_base_url',
  USE_AI_MATCHING: 'formpilot_use_ai_matching',
};

export const DEFAULT_API_BASE_URL = 'https://api.prodway.ai';

export const COMPANY_PROFILE_SCHEMA = {
  companyName: '',
  contactName: '',
  email: '',
  phone: '',
  website: '',
  address: '',
  city: '',
  state: '',
  zip: '',
  country: '',
  linkedinUrl: '',
  description: '',
};

export const MESSAGE_TYPES = {
  GET_PAGE_FIELDS: 'FORMPILOT_GET_PAGE_FIELDS',
  FILL_FIELDS: 'FORMPILOT_FILL_FIELDS',
  SUGGEST_MAPPINGS: 'FORMPILOT_SUGGEST_MAPPINGS',
};
