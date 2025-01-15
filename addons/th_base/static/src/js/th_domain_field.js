/** @odoo-module **/
import { DomainField } from '@web/views/fields/domain/domain_field';
import { registry } from "@web/core/registry";
import { _lt } from "@web/core/l10n/translation";


export class ThDomainField extends DomainField {};

ThDomainField.template = "th_base.DomainField"
registry.category("fields").add("th_domain", ThDomainField);


