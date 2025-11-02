variable "billing_account_name" {
  type        = string
  description = "Display name of the billing account. Used to configure billing alerts."
  default     = "My Billing Account"
}

variable "billing_alert_currency_code" {
  type        = string
  description = "Currency code to use for billing alerts."
  default     = "USD"
}

variable "billing_alert_amount" {
  type        = string
  description = "Amount to set for the billing alert."
  default     = "5"
}