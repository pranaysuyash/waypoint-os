"""
src/accounting/export_bridge.py — Accounting System Data Bridge (Area #17.19).

Exports commercial travel invoices and sourcing cost ledgers into:
1. Tally ERP 9 / Tally Prime XML Schema format (Sales vouchers, TCS 206C(1G), CGST/SGST/IGST ledgers).
2. Intuit QuickBooks Online REST v3 JSON Schema format (Line-item items, TaxCodes, CustomerRef).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

from src.fees.tax_compliance import CommercialInvoiceSummary


class AccountingExportBridge:
    """
    Translates Waypoint OS commercial invoices into accounting system formats.
    """

    @classmethod
    def export_tally_xml(
        cls,
        invoice: CommercialInvoiceSummary,
        customer_name: str,
        invoice_number: Optional[str] = None,
        invoice_date_yyyymmdd: Optional[str] = "20260901",
    ) -> str:
        inv_no = invoice_number or f"INV-{invoice.trip_id[:8].upper()}"
        safe_customer = escape(customer_name)

        ledger_entries_xml: List[str] = []

        # 1. Sundry Debtor (Customer Total) - Debit
        ledger_entries_xml.append(f"""
        <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{safe_customer}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{invoice.grand_total_payable_inr:.2f}</AMOUNT>
        </ALLLEDGERENTRIES.LIST>""")

        # 2. Package Tour Sales Revenue - Credit
        ledger_entries_xml.append(f"""
        <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Package Tour Sales</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{invoice.gross_package_price_inr:.2f}</AMOUNT>
        </ALLLEDGERENTRIES.LIST>""")

        # 3. GST Output Ledger - Credit
        if invoice.total_gst_inr > 0:
            ledger_entries_xml.append(f"""
        <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>GST Output Payable</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{invoice.total_gst_inr:.2f}</AMOUNT>
        </ALLLEDGERENTRIES.LIST>""")

        # 4. TCS Payable under Sec 206C(1G) - Credit
        if invoice.total_tcs_inr > 0:
            ledger_entries_xml.append(f"""
        <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>TCS Payable Sec 206C(1G)</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{invoice.total_tcs_inr:.2f}</AMOUNT>
        </ALLLEDGERENTRIES.LIST>""")

        all_ledgers = "\n".join(ledger_entries_xml)

        xml_output = f"""<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Vouchers</REPORTNAME>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER VCHTYPE="Sales" ACTION="Create">
                        <DATE>{invoice_date_yyyymmdd}</DATE>
                        <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                        <VOUCHERNUMBER>{inv_no}</VOUCHERNUMBER>
                        <PARTYLEDGERNAME>{safe_customer}</PARTYLEDGERNAME>
                        <PERSISTEDVIEW>Invoice View</PERSISTEDVIEW>
{all_ledgers}
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>"""
        return xml_output

    @classmethod
    def export_quickbooks_json(
        cls,
        invoice: CommercialInvoiceSummary,
        customer_id: str,
        customer_name: str,
        invoice_number: Optional[str] = None,
        txn_date: Optional[str] = "2026-09-01",
    ) -> Dict[str, Any]:
        inv_no = invoice_number or f"QB-INV-{invoice.trip_id[:8].upper()}"

        lines = []
        for i, item in enumerate(invoice.line_items):
            lines.append({
                "LineNum": i + 1,
                "Description": f"{item.title} ({item.supplier_name})",
                "Amount": item.gross_client_price_inr,
                "DetailType": "SalesItemLineDetail",
                "SalesItemLineDetail": {
                    "ItemRef": {
                        "value": item.service_type.upper(),
                        "name": item.service_type.title(),
                    },
                    "UnitPrice": item.gross_client_price_inr,
                    "Qty": 1,
                    "TaxCodeRef": {
                        "value": "GST_5" if item.gst_scheme.value == "TOUR_PACKAGE_5PCT" else "GST_18",
                    },
                },
            })

        # Add TCS Line if present
        if invoice.total_tcs_inr > 0:
            lines.append({
                "LineNum": len(lines) + 1,
                "Description": f"TCS under Section 206C(1G) LRS ({invoice.tcs_breakdown.effective_tcs_rate_pct}%)",
                "Amount": invoice.total_tcs_inr,
                "DetailType": "SalesItemLineDetail",
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "TCS_LRS", "name": "Tax Collected at Source"},
                    "UnitPrice": invoice.total_tcs_inr,
                    "Qty": 1,
                },
            })

        return {
            "DocNumber": inv_no,
            "TxnDate": txn_date,
            "CustomerRef": {
                "value": customer_id,
                "name": customer_name,
            },
            "TotalAmt": invoice.grand_total_payable_inr,
            "Line": lines,
            "CustomField": [
                {"DefinitionId": "1", "Name": "TripID", "Type": "StringType", "StringValue": invoice.trip_id},
                {"DefinitionId": "2", "Name": "TotalGST", "Type": "StringType", "StringValue": str(invoice.total_gst_inr)},
                {"DefinitionId": "3", "Name": "TotalTCS", "Type": "StringType", "StringValue": str(invoice.total_tcs_inr)},
            ],
        }
