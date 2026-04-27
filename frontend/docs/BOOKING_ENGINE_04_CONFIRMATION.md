# Booking Engine — Booking Confirmation

> Confirmation process, notifications, and document generation

**Series:** Booking Engine | **Document:** 4 of 8 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Confirmation Process](#confirmation-process)
3. [Document Generation](#document-generation)
4. [Notification Workflows](#notification-workflows)
5. [Supplier Booking Transmission](#supplier-booking-transmission)
6. [Confirmation Delivery Tracking](#confirmation-delivery-tracking)
7. [Post-Confirmation Actions](#post-confirmation-actions)
8. [Recovery & Retry](#recovery--retry)

---

## Overview

Booking confirmation is the critical moment when a tentative reservation becomes a committed booking. This document covers the confirmation process, document generation, notification delivery, and ensuring all parties are properly informed.

### Confirmation Checklist

| Checkpoint | Description | Status |
|------------|-------------|--------|
| **Payment Captured** | Funds secured | ✅ Required |
| **Supplier Confirmed** | All items confirmed with suppliers | ✅ Required |
| **Reference Assigned** | Unique booking reference generated | ✅ Required |
| **Documents Generated** | Vouchers, itineraries, e-tickets | ✅ Required |
| **Notifications Sent** | Email, SMS, push notifications | ⚠️ Best Effort |
| **Analytics Recorded** | Booking data in analytics | ⚠️ Best Effort |

---

## Confirmation Process

### Confirmation State Machine

```typescript
// ============================================================================
// CONFIRMATION STATE MACHINE
// ============================================================================

type ConfirmationState =
  | 'pending'
  | 'capturing_payment'
  | 'confirming_suppliers'
  | 'generating_documents'
  | 'sending_notifications'
  | 'confirmed'
  | 'partial'
  | 'failed';

interface ConfirmationContext {
  booking: Booking;
  paymentResult?: PaymentResult;
  supplierConfirmations: SupplierConfirmation[];
  documents: GeneratedDocument[];
  notifications: NotificationResult[];
  errors: ConfirmationError[];
}

class ConfirmationOrchestrator {
  async confirmBooking(bookingId: string): Promise<ConfirmationResult> {
    const context: ConfirmationContext = {
      booking: await Booking.findById(bookingId),
      supplierConfirmations: [],
      documents: [],
      notifications: [],
      errors: [],
    };

    // Validate preconditions
    await this.validatePreconditions(context);

    try {
      // Step 1: Capture payment
      await this.transitionTo('capturing_payment', context);
      context.paymentResult = await this.capturePayment(context);

      // Step 2: Confirm with suppliers
      await this.transitionTo('confirming_suppliers', context);
      context.supplierConfirmations = await this.confirmSuppliers(context);

      // Step 3: Generate documents
      await this.transitionTo('generating_documents', context);
      context.documents = await this.generateDocuments(context);

      // Step 4: Send notifications
      await this.transitionTo('sending_notifications', context);
      context.notifications = await this.sendNotifications(context);

      // Step 5: Finalize
      await this.transitionTo('confirmed', context);
      await this.finalizeConfirmation(context);

      return {
        success: true,
        booking: context.booking,
        documents: context.documents,
        notifications: context.notifications,
      };

    } catch (error) {
      context.errors.push({
        step: context.booking.state,
        error: error.message,
        timestamp: new Date(),
      });

      await this.handleConfirmationFailure(context, error);
      throw error;
    }
  }

  private async transitionTo(
    state: ConfirmationState,
    context: ConfirmationContext
  ): Promise<void> {
    const previousState = context.booking.state;
    context.booking.state = state;
    context.booking.updatedAt = new Date();

    await this.recordStateTransition(context.booking, previousState, state);
    await context.booking.save();
  }

  private async validatePreconditions(context: ConfirmationContext): Promise<void> {
    const { booking } = context;

    // Check booking status
    if (booking.status !== 'pending') {
      throw new InvalidBookingStatusError(booking.status, 'pending');
    }

    // Check payment authorization
    const payment = await BookingPayment.findOne({
      bookingId: booking.id,
      status: 'authorized',
    });

    if (!payment) {
      throw new PaymentNotAuthorizedError();
    }

    // Check inventory holds
    const holds = await InventoryHold.find({
      bookingId: booking.id,
      status: 'active',
    });

    if (holds.length !== booking.items.length) {
      throw new IncompleteHoldsError(holds.length, booking.items.length);
    }

    // Check price lock validity
    const lockValid = await this.verifyPriceLock(booking);
    if (!lockValid) {
      throw new PriceLockExpiredError();
    }
  }

  private async capturePayment(
    context: ConfirmationContext
  ): Promise<PaymentResult> {
    const { booking } = context;
    const payments = await BookingPayment.find({
      bookingId: booking.id,
      status: 'authorized',
    });

    const results: PaymentResult[] = [];

    for (const payment of payments) {
      try {
        const capture = await PaymentService.capture(payment.paymentId);

        payment.status = 'captured';
        payment.capturedAt = new Date();
        await payment.save();

        results.push({
          paymentId: payment.paymentId,
          status: 'captured',
          amount: payment.amount,
        });

      } catch (error) {
        await this.handlePaymentFailure(payment, error);
        throw new PaymentCaptureError(payment.paymentId, error.message);
      }
    }

    booking.paymentStatus = 'paid';
    await booking.save();

    return {
      status: 'captured',
      total: results.reduce((sum, r) => sum + r.amount, 0),
      payments: results,
    };
  }

  private async confirmSuppliers(
    context: ConfirmationContext
  ): Promise<SupplierConfirmation[]> {
    const { booking } = context;
    const confirmations: SupplierConfirmation[] = [];

    // Convert holds to confirmed
    const holds = await InventoryHold.find({
      bookingId: booking.id,
      status: 'active',
    });

    for (const hold of holds) {
      const item = booking.items.find(i => i.id === hold.bookingItemId);

      try {
        // Confirm with supplier
        const supplierBooking = await this.confirmSupplierBooking(booking, item, hold);

        // Update hold
        hold.type = 'confirmed';
        hold.status = 'confirmed';
        hold.confirmedAt = new Date();
        hold.expiresAt = null;
        await hold.save();

        // Update item
        item.status = 'confirmed';
        item.supplierReference = supplierBooking.reference;
        item.confirmationCode = supplierBooking.confirmationCode;
        item.confirmedAt = new Date();
        await item.save();

        confirmations.push({
          itemId: item.id,
          supplierId: hold.supplierId,
          reference: supplierBooking.reference,
          confirmationCode: supplierBooking.confirmationCode,
          status: 'confirmed',
        });

      } catch (error) {
        logger.error('Supplier confirmation failed', {
          bookingId: booking.id,
          itemId: item.id,
          supplierId: hold.supplierId,
          error,
        });

        confirmations.push({
          itemId: item.id,
          supplierId: hold.supplierId,
          status: 'failed',
          error: error.message,
        });
      }
    }

    // Check if all items confirmed
    const allConfirmed = confirmations.every(c => c.status === 'confirmed');
    const someConfirmed = confirmations.some(c => c.status === 'confirmed');

    if (allConfirmed) {
      booking.status = 'confirmed';
    } else if (someConfirmed) {
      booking.status = 'partial';
    } else {
      booking.status = 'failed';
      throw new AllSupplierConfirmationFailedError();
    }

    await booking.save();

    return confirmations;
  }

  private async confirmSupplierBooking(
    booking: Booking,
    item: BookingItem,
    hold: InventoryHold
  ): Promise<SupplierBookingResult> {
    const supplier = await SupplierService.get(hold.supplierId);

    // If hold already has supplier reference, just confirm
    if (hold.supplierHoldId) {
      return await SupplierService.confirmHold({
        supplierId: hold.supplierId,
        holdId: hold.supplierHoldId,
        bookingDetails: this.buildBookingDetails(booking, item),
      });
    }

    // Otherwise, create new booking
    return await SupplierService.createBooking({
      supplierId: hold.supplierId,
      request: {
        ...this.buildBookingDetails(booking, item),
        holdId: hold.supplierHoldId,
      },
    });
  }

  private buildBookingDetails(
    booking: Booking,
    item: BookingItem
  ): SupplierBookingRequest {
    return {
      reference: booking.reference,
      customer: {
        name: `${booking.customerInfo.primary.firstName} ${booking.customerInfo.primary.lastName}`,
        email: booking.customerInfo.primary.email,
        phone: booking.customerInfo.primary.phone,
      },
      dates: {
        start: item.dates.start,
        end: item.dates.end,
      },
      travelers: booking.customerInfo.travelers.map(t => ({
        title: t.title,
        firstName: t.firstName,
        lastName: t.lastName,
        dateOfBirth: t.dateOfBirth,
        nationality: t.nationality,
        passport: t.passport,
      })),
    };
  }

  private async finalizeConfirmation(
    context: ConfirmationContext
  ): Promise<void> {
    const { booking } = context;

    // Generate booking reference if not exists
    if (!booking.reference) {
      booking.reference = await this.generateBookingReference();
    }

    // Update timestamps
    booking.confirmedAt = new Date();
    booking.status = booking.status === 'partial' ? 'partial' : 'confirmed';
    booking.state = 'confirmed';
    booking.version += 1;

    await booking.save();

    // Record confirmation event
    await BookingEvent.create({
      bookingId: booking.id,
      type: 'booking.confirmed',
      state: booking.state,
      data: {
        reference: booking.reference,
        confirmedAt: booking.confirmedAt,
        itemsConfirmed: context.supplierConfirmations.filter(c => c.status === 'confirmed').length,
        itemsFailed: context.supplierConfirmations.filter(c => c.status === 'failed').length,
      },
      correlationId: booking.id,
      actorType: 'system',
      actorId: 'booking-engine',
    });

    // Update analytics
    await Analytics.track('booking_confirmed', {
      bookingId: booking.id,
      reference: booking.reference,
      total: booking.pricing.total,
      itemCount: booking.items.length,
    });
  }

  private async generateBookingReference(): Promise<string> {
    // Format: TRV-YYYY-XXXX (base32 encoded)
    const year = new Date().getFullYear();
    const key = `booking-ref:${year}`;

    const sequence = await Redis.incr(key);
    const code = base32Encode(sequence).padStart(4, '0').toUpperCase().slice(0, 4);

    return `TRV-${year}-${code}`;
  }
}
```

---

## Document Generation

### Document Types

```typescript
// ============================================================================
// DOCUMENT TYPES
// ============================================================================

type DocumentType =
  | 'itinerary'           // Full trip itinerary
  | 'voucher'             // Accommodation/activity voucher
  | 'eticket'             // Flight e-ticket
  | 'invoice'             // Payment invoice
  | 'receipt'             // Payment receipt
  | 'cancellation_policy' // Cancellation terms
  | 'travel_docs';        // Combined travel document

interface GeneratedDocument {
  id: string;
  bookingId: string;
  type: DocumentType;
  format: 'pdf' | 'html' | 'json';
  url: string;
  filename: string;
  size: number;
  language: string;
  generatedAt: Date;
}

class DocumentGenerator {
  private storage: StorageService;
  private renderer: DocumentRenderer;

  async generateForBooking(booking: Booking): Promise<GeneratedDocument[]> {
    const documents: GeneratedDocument[] = [];

    // 1. Main itinerary
    const itinerary = await this.generateItinerary(booking);
    documents.push(itinerary);

    // 2. Item-specific documents
    for (const item of booking.items) {
      if (item.type === 'accommodation') {
        const voucher = await this.generateHotelVoucher(booking, item);
        documents.push(voucher);
      } else if (item.type === 'flight') {
        const eticket = await this.generateETicket(booking, item);
        documents.push(eturket);
      } else if (item.type === 'activity') {
        const voucher = await this.generateActivityVoucher(booking, item);
        documents.push(voucher);
      }
    }

    // 3. Invoice
    const invoice = await this.generateInvoice(booking);
    documents.push(invoice);

    // 4. Cancellation policy
    const policy = await this.generateCancellationPolicy(booking);
    documents.push(policy);

    // 5. Combined travel document (optional)
    const combined = await this.generateCombinedDocument(booking, documents);
    documents.push(combined);

    return documents;
  }

  private async generateItinerary(booking: Booking): Promise<GeneratedDocument> {
    const data = {
      reference: booking.reference,
      customer: booking.customerInfo.primary,
      travelers: booking.customerInfo.travelers,
      items: booking.items.map(item => ({
        type: item.type,
        name: this.getItemName(item),
        dates: item.dates,
        confirmationCode: item.confirmationCode,
        details: this.getItemDetails(item),
      })),
      pricing: booking.pricing,
      payments: await this.getPaymentSummary(booking),
      importantInfo: await this.getImportantInfo(booking),
      contactInfo: await this.getContactInfo(booking),
      terms: await this.getBookingTerms(booking),
    };

    const html = await this.renderer.render('itinerary', data);
    const pdf = await this.renderer.toPDF(html);

    const filename = `itinerary-${booking.reference}.pdf`;
    const url = await this.storage.upload(filename, pdf, 'application/pdf');

    return await BookingDocument.create({
      bookingId: booking.id,
      type: 'itinerary',
      format: 'pdf',
      url,
      filename,
      size: pdf.length,
      language: 'en',
      generatedAt: new Date(),
    });
  }

  private async generateHotelVoucher(
    booking: Booking,
    item: BookingItem
  ): Promise<GeneratedDocument> {
    const data = {
      reference: booking.reference,
      voucherNumber: `${booking.reference}-HOT${item.id.slice(-4)}`,
      hotel: item.accommodation,
      dates: item.dates,
      guests: booking.customerInfo.travelers,
      roomType: item.accommodation?.roomType,
      mealPlan: item.accommodation?.mealPlan,
      confirmationCode: item.confirmationCode,
      supplierReference: item.supplierReference,
      checkInInstructions: await this.getCheckInInstructions(item),
      cancellationPolicy: item.cancellation,
      pricing: item.pricing,
      paid: true,
      logo: await this.getSupplierLogo(item.supplierId),
    };

    const html = await this.renderer.render('hotel-voucher', data);
    const pdf = await this.renderer.toPDF(html);

    const filename = `voucher-${item.type}-${booking.reference}.pdf`;
    const url = await this.storage.upload(filename, pdf, 'application/pdf');

    return await BookingDocument.create({
      bookingId: booking.id,
      itemId: item.id,
      type: 'voucher',
      format: 'pdf',
      url,
      filename,
      size: pdf.length,
      language: 'en',
      generatedAt: new Date(),
    });
  }

  private async generateETicket(
    booking: Booking,
    item: BookingItem
  ): Promise<GeneratedDocument> {
    const data = {
      reference: booking.reference,
      ticketNumber: item.flight?.ticketNumber || `${booking.reference}-FLT${item.id.slice(-4)}`,
      passengerName: `${booking.customerInfo.primary.firstName} ${booking.customerInfo.primary.lastName}`.toUpperCase(),
      flights: item.flight?.segments.map(seg => ({
        airline: seg.airline,
        flightNumber: seg.flightNumber,
        departure: {
          airport: seg.departure.airport,
          airportCode: seg.departure.code,
          date: format(seg.departure.date, 'DD MMM YYYY'),
          time: format(seg.departure.date, 'HH:mm'),
          terminal: seg.departure.terminal,
        },
        arrival: {
          airport: seg.arrival.airport,
          airportCode: seg.arrival.code,
          date: format(seg.arrival.date, 'DD MMM YYYY'),
          time: format(seg.arrival.date, 'HH:mm'),
          terminal: seg.arrival.terminal,
        },
        class: seg.cabinClass,
        aircraft: seg.aircraft,
        duration: seg.duration,
      })),
      confirmationCode: item.confirmationCode,
      bookingClass: item.flight?.bookingClass,
      fareBasis: item.flight?.fareBasis,
      baggage: item.flight?.baggage,
      seat: item.flight?.seat,
      frequentFlyer: booking.customerInfo.primary.frequentFlyer,
      pricing: item.pricing,
      paid: true,
      barcode: this.generateETicketBarcode(item),
    };

    const html = await this.renderer.render('eticket', data);
    const pdf = await this.renderer.toPDF(html);

    const filename = `eticket-${booking.reference}.pdf`;
    const url = await this.storage.upload(filename, pdf, 'application/pdf');

    return await BookingDocument.create({
      bookingId: booking.id,
      itemId: item.id,
      type: 'eticket',
      format: 'pdf',
      url,
      filename,
      size: pdf.length,
      language: 'en',
      generatedAt: new Date(),
    });
  }

  private async generateInvoice(booking: Booking): Promise<GeneratedDocument> {
    const payments = await BookingPayment.find({ bookingId: booking.id });

    const data = {
      invoiceNumber: `INV-${booking.reference}`,
      invoiceDate: new Date(),
      dueDate: booking.confirmedAt, // Already paid
      billedTo: {
        name: `${booking.customerInfo.primary.firstName} ${booking.customerInfo.primary.lastName}`,
        email: booking.customerInfo.primary.email,
        address: booking.customerInfo.billing,
      },
      items: booking.items.map(item => ({
        description: this.getItemName(item),
        dates: `${format(item.dates.start, 'DD MMM YYYY')} - ${format(item.dates.end, 'DD MMM YYYY')}`,
        quantity: 1,
        unitPrice: item.pricing.baseRate,
        tax: item.pricing.taxes,
        total: item.pricing.total,
      })),
      subtotal: booking.pricing.subtotal,
      taxes: booking.pricing.taxes,
      fees: booking.pricing.fees,
      discount: booking.pricing.discount,
      total: booking.pricing.total,
      payments: payments.map(p => ({
        method: p.method,
        amount: p.amount,
        date: p.createdAt,
        transactionId: p.transactionId,
      })),
      paidInFull: true,
      currency: booking.pricing.currency,
      companyInfo: await this.getCompanyInfo(),
    };

    const html = await this.renderer.render('invoice', data);
    const pdf = await this.renderer.toPDF(html);

    const filename = `invoice-${booking.reference}.pdf`;
    const url = await this.storage.upload(filename, pdf, 'application/pdf');

    return await BookingDocument.create({
      bookingId: booking.id,
      type: 'invoice',
      format: 'pdf',
      url,
      filename,
      size: pdf.length,
      language: 'en',
      generatedAt: new Date(),
    });
  }

  private async generateCombinedDocument(
    booking: Booking,
    documents: GeneratedDocument[]
  ): Promise<GeneratedDocument> {
    // Create a single PDF with all documents combined
    const pdfBuffers = await Promise.all(
      documents.map(d => this.storage.download(d.url))
    );

    const combined = await this.mergePDFs(pdfBuffers);

    const filename = `travel-docs-${booking.reference}.pdf`;
    const url = await this.storage.upload(filename, combined, 'application/pdf');

    return await BookingDocument.create({
      bookingId: booking.id,
      type: 'travel_docs',
      format: 'pdf',
      url,
      filename,
      size: combined.length,
      language: 'en',
      generatedAt: new Date(),
    });
  }

  private generateETicketBarcode(item: BookingItem): string {
    // IATA standard barcode data
    const data = {
      m: item.confirmationCode, // Mobile boarding pass
      n: item.flight?.segments.map(s => s.flightNumber).join(' '),
      t: item.flight?.segments.map(s => format(s.departure.date, 'DDMMMHHmm', { code: 'en' })).join(' '),
    };

    return JSON.stringify(data);
  }

  private getItemName(item: BookingItem): string {
    switch (item.type) {
      case 'accommodation':
        return item.accommodation?.name || 'Accommodation';
      case 'flight':
        return `${item.flight?.segments[0].departure.code} → ${item.flight?.segments[item.flight.segments.length - 1].arrival.code}`;
      case 'transfer':
        return item.transfer?.description || 'Transfer';
      case 'activity':
        return item.activity?.name || 'Activity';
      default:
        return 'Booking Item';
    }
  }

  private getItemDetails(item: BookingItem): Record<string, unknown> {
    switch (item.type) {
      case 'accommodation':
        return {
          address: item.accommodation?.address,
          phone: item.accommodation?.phone,
          email: item.accommodation?.email,
          checkIn: item.accommodation?.checkIn,
          checkOut: item.accommodation?.checkOut,
        };
      case 'flight':
        return {
          airline: item.flight?.segments[0].airline,
          flightNumbers: item.flight?.segments.map(s => s.flightNumber).join(', '),
          duration: item.flight?.duration,
        };
      default:
        return {};
    }
  }
}
```

### Document Templates

```typescript
// ============================================================================
// DOCUMENT TEMPLATES
// ============================================================================

// Itinerary template structure (HTML)
const ITINERARY_TEMPLATE = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; }
    .header { background: #1a1a1a; color: white; padding: 20px; }
    .logo { max-width: 150px; }
    .title { font-size: 24px; margin: 20px 0; }
    .section { margin: 30px 0; padding: 20px; border: 1px solid #eee; }
    .item { margin: 15px 0; padding: 15px; background: #f9f9f9; }
    .total { font-size: 18px; font-weight: bold; text-align: right; }
    .footer { margin-top: 40px; padding: 20px; background: #f5f5f5; font-size: 12px; }
  </style>
</head>
<body>
  <div class="header">
    <img src="{{logo}}" class="logo" alt="Logo">
    <h1>Travel Itinerary</h1>
    <p>Reference: {{reference}}</p>
  </div>

  <div class="section">
    <h2>Traveler Information</h2>
    <p>{{customer.firstName}} {{customer.lastName}}</p>
    <p>{{customer.email}} | {{customer.phone}}</p>
  </div>

  <div class="section">
    <h2>Booking Details</h2>
    {{#each items}}
    <div class="item">
      <h3>{{type}}: {{name}}</h3>
      <p>Dates: {{dates.start}} - {{dates.end}}</p>
      <p>Confirmation: {{confirmationCode}}</p>
    </div>
    {{/each}}
  </div>

  <div class="section">
    <h2>Payment Summary</h2>
    <p>Total Paid: {{pricing.total}} {{pricing.currency}}</p>
  </div>

  <div class="footer">
    <p>Generated: {{generatedAt}}</p>
    <p>For questions, contact: {{contactInfo.email}} | {{contactInfo.phone}}</p>
  </div>
</body>
</html>
`;
```

---

## Notification Workflows

### Multi-Channel Notifications

```typescript
// ============================================================================
// NOTIFICATION SERVICE
// ============================================================================

interface NotificationChannel {
  type: 'email' | 'sms' | 'push' | 'webhook';
  enabled: boolean;
  priority: number;
}

interface NotificationRequest {
  bookingId: string;
  type: NotificationType;
  channels: NotificationChannel[];
  data: Record<string, unknown>;
}

type NotificationType =
  | 'booking_confirmed'
  | 'booking_partial'
  | 'booking_failed'
  | 'payment_received'
  | 'document_ready'
  | 'reminder'
  | 'cancellation'
  | 'modification';

class NotificationOrchestrator {
  async sendBookingConfirmation(booking: Booking): Promise<NotificationSummary> {
    const documents = await BookingDocument.find({ bookingId: booking.id });
    const summary: NotificationSummary = {
      email: { sent: false, error: null },
      sms: { sent: false, error: null },
      push: { sent: false, error: null },
      webhook: { sent: false, error: null },
    };

    // 1. Email (primary channel)
    try {
      await this.sendConfirmationEmail(booking, documents);
      summary.email.sent = true;
    } catch (error) {
      summary.email.error = error.message;
      logger.error('Confirmation email failed', { bookingId: booking.id, error });
    }

    // 2. SMS (if opted in)
    if (booking.customerInfo.preferences?.sms) {
      try {
        await this.sendConfirmationSMS(booking);
        summary.sms.sent = true;
      } catch (error) {
        summary.sms.error = error.message;
        logger.error('Confirmation SMS failed', { bookingId: booking.id, error });
      }
    }

    // 3. Push notification (if mobile)
    if (booking.metadata.deviceTokens?.length > 0) {
      try {
        await this.sendConfirmationPush(booking);
        summary.push.sent = true;
      } catch (error) {
        summary.push.error = error.message;
        logger.error('Confirmation push failed', { bookingId: booking.id, error });
      }
    }

    // 4. Webhook (for integrations)
    if (booking.metadata.webhookUrl) {
      try {
        await this.sendConfirmationWebhook(booking, documents);
        summary.webhook.sent = true;
      } catch (error) {
        summary.webhook.error = error.message;
        // Retry webhook in background
        await this.queueWebhookRetry(booking.metadata.webhookUrl, {
          type: 'booking.confirmed',
          booking: booking.toPayload(),
        });
      }
    }

    // Record notification results
    await this.recordNotificationResults(booking.id, summary);

    return summary;
  }

  private async sendConfirmationEmail(
    booking: Booking,
    documents: GeneratedDocument[]
  ): Promise<void> {
    const template = await EmailTemplate.get('booking-confirmed');

    const email = {
      to: booking.customerInfo.primary.email,
      cc: booking.metadata.source === 'agent' ? booking.metadata.agentEmail : undefined,
      subject: template.renderSubject({ reference: booking.reference }),
      html: template.renderBody({
        customerName: booking.customerInfo.primary.firstName,
        reference: booking.reference,
        items: booking.items,
        total: booking.pricing.total,
        documents: documents.map(d => ({ type: d.type, url: d.url, filename: d.filename })),
        viewBookingUrl: `${process.env.APP_URL}/bookings/${booking.id}`,
        manageBookingUrl: `${process.env.APP_URL}/bookings/${booking.id}/manage`,
      }),
      attachments: await this.getDocumentAttachments(documents),
      metadata: {
        bookingId: booking.id,
        type: 'booking_confirmed',
      },
    };

    await EmailService.send(email);
  }

  private async sendConfirmationSMS(booking: Booking): Promise<void> {
    const template = await SMSTemplate.get('booking-confirmed');

    const message = template.render({
      reference: booking.reference,
      total: booking.pricing.total,
      viewUrl: `${process.env.APP_URL}/bookings/${booking.id}`,
    });

    await SMSService.send({
      to: booking.customerInfo.primary.phone,
      message,
      metadata: {
        bookingId: booking.id,
        type: 'booking_confirmed',
      },
    });
  }

  private async sendConfirmationPush(booking: Booking): Promise<void> {
    await PushService.send({
      tokens: booking.metadata.deviceTokens,
      notification: {
        title: 'Booking Confirmed! ✈️',
        body: `Your trip ${booking.reference} has been confirmed. View your itinerary now.`,
        icon: 'booking_confirmed',
        badge: 1,
      },
      data: {
        type: 'booking_confirmed',
        bookingId: booking.id,
        reference: booking.reference,
        url: `/bookings/${booking.id}`,
      },
    });
  }

  private async sendConfirmationWebhook(
    booking: Booking,
    documents: GeneratedDocument[]
  ): Promise<void> {
    await HTTPClient.post(booking.metadata.webhookUrl, {
      event: 'booking.confirmed',
      timestamp: new Date().toISOString(),
      data: {
        booking: {
          id: booking.id,
          reference: booking.reference,
          status: booking.status,
          total: booking.pricing.total,
          currency: booking.pricing.currency,
        },
        customer: {
          id: booking.customerId,
          email: booking.customerInfo.primary.email,
          phone: booking.customerInfo.primary.phone,
        },
        items: booking.items.map(item => ({
          id: item.id,
          type: item.type,
          status: item.status,
          confirmationCode: item.confirmationCode,
        })),
        documents: documents.map(d => ({
          type: d.type,
          url: d.url,
        })),
      },
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': this.generateWebhookSignature(booking),
      },
      timeout: 10000,
    });
  }

  private async queueWebhookRetry(
    url: string,
    payload: Record<string, unknown>
  ): Promise<void> {
    await Queue.add('webhook-retry', {
      url,
      payload,
      attempt: 0,
      maxAttempts: 5,
      backoff: {
        type: 'exponential',
        delay: 60000, // Start with 1 minute
      },
    });
  }
}

// ============================================================================
// NOTIFICATION TEMPLATES
// ============================================================================

const EMAIL_TEMPLATES = {
  'booking-confirmed': {
    subject: 'Booking Confirmed: {{reference}}',
    body: `
      <h1>Booking Confirmed! 🎉</h1>

      <p>Hi {{customerName}},</p>

      <p>Great news! Your booking <strong>{{reference}}</strong> has been confirmed.</p>

      <h2>Your Trip</h2>
      {{#each items}}
      <p><strong>{{type}}:</strong> {{name}}<br>
      {{dates.start}} - {{dates.end}}<br>
      Confirmation: {{confirmationCode}}</p>
      {{/each}}

      <h2>Payment</h2>
      <p>Total Paid: <strong>{{total}}</strong></p>

      <h2>Documents</h2>
      {{#each documents}}
      <p><a href="{{url}}">{{filename}}</a></p>
      {{/each}}

      <p>
        <a href="{{viewBookingUrl}}" class="button">View Full Itinerary</a>
      </p>

      <p>Need to make changes? <a href="{{manageBookingUrl}}">Manage your booking</a></p>

      <hr>
      <p>Questions? Contact us at support@example.com</p>
    `,
  },

  'booking-partial': {
    subject: 'Booking Update: {{reference}}',
    body: `
      <h1>Booking Update</h1>

      <p>Hi {{customerName}},</p>

      <p>Your booking <strong>{{reference}}</strong> has been partially confirmed.</p>

      <h2>Confirmed Items</h2>
      {{#each confirmedItems}}
      <p>✓ {{name}} - {{confirmationCode}}</p>
      {{/each}}

      <h2>Pending Items</h2>
      {{#each pendingItems}}
      <p>⏳ {{name}} - Awaiting confirmation</p>
      {{/each}}

      <p>We'll notify you as soon as the remaining items are confirmed.</p>
    `,
  },
};
```

---

## Supplier Booking Transmission

### Supplier API Integration

```typescript
// ============================================================================
// SUPPLIER BOOKING TRANSMISSION
// ============================================================================

interface SupplierBookingRequest {
  supplierId: string;
  holdId?: string;
  bookingDetails: {
    reference: string;
    customer: CustomerDetails;
    dates: DateRange;
    travelers: TravelerDetails[];
    specialRequests?: string[];
  };
}

interface SupplierBookingResponse {
  success: boolean;
  reference?: string;
  confirmationCode?: string;
  pending?: boolean;
  error?: string;
  documents?: string[];
}

class SupplierBookingClient {
  private clients: Map<string, SupplierClient>;

  async transmitBooking(
    item: BookingItem,
    booking: Booking
  ): Promise<SupplierBookingResponse> {
    const client = this.getClientForSupplier(item.supplierId);

    // Transform booking data to supplier format
    const request = this.buildSupplierRequest(item, booking);

    // Call supplier API
    const response = await client.createBooking(request);

    // Handle response
    if (response.success) {
      // Store supplier reference
      item.supplierReference = response.reference;
      item.confirmationCode = response.confirmationCode;
      await item.save();

      // Queue document retrieval if provided
      if (response.documents) {
        await this.queueDocumentRetrieval(item, response.documents);
      }
    }

    return response;
  }

  private buildSupplierRequest(
    item: BookingItem,
    booking: Booking
  ): SupplierBookingRequest {
    const baseRequest = {
      supplierId: item.supplierId,
      bookingDetails: {
        reference: booking.reference,
        customer: {
          name: `${booking.customerInfo.primary.firstName} ${booking.customerInfo.primary.lastName}`,
          email: booking.customerInfo.primary.email,
          phone: booking.customerInfo.primary.phone,
          language: 'en',
        },
        dates: item.dates,
        travelers: booking.customerInfo.travelers.map(t => ({
          title: t.title,
          firstName: t.firstName,
          lastName: t.lastName,
          dateOfBirth: t.dateOfBirth,
          nationality: t.nationality,
          passportNumber: t.passport?.number,
          passportExpiry: t.passport?.expiry,
        })),
      },
    };

    // Add type-specific details
    switch (item.type) {
      case 'accommodation':
        return {
          ...baseRequest,
          bookingDetails: {
            ...baseRequest.bookingDetails,
            roomType: item.accommodation?.roomType,
            mealPlan: item.accommodation?.mealPlan,
            specialRequests: item.accommodation?.specialRequests,
            guaranteed: true, // Payment already taken
          },
        };

      case 'flight':
        return {
          ...baseRequest,
          bookingDetails: {
            ...baseRequest.bookingDetails,
            segments: item.flight?.segments.map(s => ({
              airline: s.airline,
              flightNumber: s.flightNumber,
              departure: {
                airport: s.departure.code,
                date: s.departure.date,
                terminal: s.departure.terminal,
              },
              arrival: {
                airport: s.arrival.code,
                date: s.arrival.date,
                terminal: s.arrival.terminal,
              },
              cabinClass: s.cabinClass,
              bookingClass: s.bookingClass,
            })),
            ssr: item.flight?.specialServices,
          },
        };

      default:
        return baseRequest;
    }
  }

  private async queueDocumentRetrieval(
    item: BookingItem,
    documentUrls: string[]
  ): Promise<void> {
    await Queue.add('retrieve-supplier-documents', {
      itemId: item.id,
      documentUrls,
    });
  }
}
```

---

## Confirmation Delivery Tracking

### Delivery Status

```typescript
// ============================================================================
// DELIVERY TRACKING
// ============================================================================

interface DeliveryStatus {
  bookingId: string;
  channel: 'email' | 'sms' | 'push' | 'webhook';
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced';
  sentAt?: Date;
  deliveredAt?: Date;
  failedAt?: Date;
  error?: string;
  retryCount: number;
  metadata: Record<string, unknown>;
}

class DeliveryTracker {
  async trackEmail(
    bookingId: string,
    messageId: string
  ): Promise<DeliveryStatus> {
    // Wait for delivery webhook from email provider
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        resolve({
          bookingId,
          channel: 'email',
          status: 'sent',
          sentAt: new Date(),
          retryCount: 0,
          metadata: { messageId },
        });
      }, 5000); // Assume sent if no webhook in 5s

      // Listen for webhook
      this.webhookHandler.on(`email:${messageId}`, (event) => {
        clearTimeout(timeout);

        if (event.event === 'delivered') {
          resolve({
            bookingId,
            channel: 'email',
            status: 'delivered',
            sentAt: new Date(event.timestamp),
            deliveredAt: new Date(event.timestamp),
            retryCount: 0,
            metadata: { messageId, event },
          });
        } else if (event.event === 'bounced') {
          resolve({
            bookingId,
            channel: 'email',
            status: 'bounced',
            sentAt: new Date(event.timestamp),
            failedAt: new Date(event.timestamp),
            error: event.reason,
            retryCount: 0,
            metadata: { messageId, event },
          });
        }
      });
    });
  }

  async checkDeliveryStatus(bookingId: string): Promise<DeliveryStatus[]> {
    return await DeliveryStatus.find({ bookingId });
  }

  async getUndeliveredBookings(): Promise<string[]> {
    const undelivered = await DeliveryStatus.find({
      status: { $in: ['pending', 'failed'] },
      sentAt: { $lt: subHours(new Date(), 1) },
    });

    return [...new Set(undelivered.map(d => d.bookingId))];
  }
}
```

---

## Post-Confirmation Actions

### Automated Follow-ups

```typescript
// ============================================================================
// POST-CONFIRMATION ACTIONS
// ============================================================================

class PostConfirmationProcessor {
  async process(booking: Booking): Promise<void> {
    // Queue all post-confirmation tasks
    await Promise.all([
      this.queueWelcomeEmail(booking),
      this.queueTravelGuide(booking),
      this.queueSupplierUpdates(booking),
      this.queueCRMUpdate(booking),
      this.queueAnalyticsEvents(booking),
    ]);
  }

  private async queueWelcomeEmail(booking: Booking): Promise<void> {
    // Send 1 hour after confirmation
    await Agenda.schedule('welcome-email', new Date(Date.now() + 3600000), {
      bookingId: booking.id,
      customerId: booking.customerId,
    });
  }

  private async queueTravelGuide(booking: Booking): Promise<void> {
    // Send destination-specific guides
    const destinations = this.extractDestinations(booking);

    for (const destination of destinations) {
      await Agenda.schedule('travel-guide', new Date(Date.now() + 7200000), {
        bookingId: booking.id,
        destination,
      });
    }
  }

  private async queueSupplierUpdates(booking: Booking): Promise<void> {
    // Update supplier CRM systems
    for (const item of booking.items) {
      await Queue.add('supplier-crm-update', {
        supplierId: item.supplierId,
        bookingId: booking.id,
        itemId: item.id,
        customer: booking.customerInfo.primary,
        value: item.pricing.total,
      });
    }
  }

  private async queueCRMUpdate(booking: Booking): Promise<void> {
    // Update our CRM
    await CRMService.updateCustomer(booking.customerId, {
      lastBookingDate: booking.confirmedAt,
      totalBookings: { $inc: 1 },
      totalSpend: { $inc: booking.pricing.total },
    });
  }

  private async queueAnalyticsEvents(booking: Booking): Promise<void> {
    await Analytics.track('booking_confirmed', {
      bookingId: booking.id,
      reference: booking.reference,
      total: booking.pricing.total,
      currency: booking.pricing.currency,
      itemCount: booking.items.length,
      destination: this.getPrimaryDestination(booking),
      channel: booking.metadata.channel,
      source: booking.metadata.source,
    });
  }

  private extractDestinations(booking: Booking): string[] {
    const destinations = new Set<string>();

    for (const item of booking.items) {
      if (item.accommodation?.destination) {
        destinations.add(item.accommodation.destination);
      }
      if (item.activity?.destination) {
        destinations.add(item.activity.destination);
      }
      // Flight destinations
      if (item.flight?.segments) {
        for (const seg of item.flight.segments) {
          destinations.add(seg.arrival.city);
        }
      }
    }

    return Array.from(destinations);
  }
}
```

---

## Recovery & Retry

### Failed Confirmation Recovery

```typescript
// ============================================================================
// RECOVERY PROCEDURES
// ============================================================================

class ConfirmationRecovery {
  async recoverFailedConfirmation(bookingId: string): Promise<void> {
    const booking = await Booking.findById(bookingId);

    if (booking.status !== 'failed') {
      throw new InvalidBookingStatusError(booking.status, 'failed');
    }

    // Analyze failure
    const failure = await this.analyzeFailure(booking);

    // Attempt recovery based on failure type
    switch (failure.type) {
      case 'payment_failed':
        await this.recoverPayment(booking, failure);
        break;

      case 'supplier_failed':
        await this.recoverSupplierBooking(booking, failure);
        break;

      case 'partial_confirmation':
        await this.recoverPartialConfirmation(booking, failure);
        break;

      default:
        throw new UnrecoverableError(failure.type);
    }
  }

  private async analyzeFailure(booking: Booking): Promise<FailureAnalysis> {
    const events = await BookingEvent.find({
      bookingId: booking.id,
      type: { $in: ['payment.failed', 'supplier.failed', 'booking.failed'] },
    }).sort({ timestamp: -1 });

    const lastEvent = events[0];

    if (lastEvent.type === 'payment.failed') {
      return {
        type: 'payment_failed',
        recoverable: true,
        data: lastEvent.data,
      };
    }

    if (lastEvent.type === 'supplier.failed') {
      return {
        type: 'supplier_failed',
        recoverable: true,
        data: lastEvent.data,
      };
    }

    return {
      type: 'unknown',
      recoverable: false,
      data: lastEvent.data,
    };
  }

  private async recoverPayment(
    booking: Booking,
    failure: FailureAnalysis
  ): Promise<void> {
    // Check if payment can be retried
    const payment = await BookingPayment.findOne({
      bookingId: booking.id,
      status: 'failed',
    });

    if (!payment) {
      throw new PaymentNotFoundError();
    }

    // Check if payment method allows retry
    const canRetry = await PaymentService.canRetry(payment.paymentMethodId);

    if (!canRetry) {
      // Request alternative payment method
      await this.requestAlternativePayment(booking);
      return;
    }

    // Retry payment
    const retry = await PaymentService.retry(payment.paymentId);

    if (retry.status === 'succeeded') {
      // Continue with confirmation
      await new ConfirmationOrchestrator().confirmBooking(booking.id);
    }
  }

  private async recoverSupplierBooking(
    booking: Booking,
    failure: FailureAnalysis
  ): Promise<void> {
    const failedItemId = failure.data.itemId;
    const item = booking.items.find(i => i.id === failedItemId);

    if (!item) {
      throw new ItemNotFoundError(failedItemId);
    }

    // Try alternative supplier
    const alternatives = await this.findAlternativeSuppliers(item);

    if (alternatives.length > 0) {
      // Offer alternatives to customer
      await this.offerAlternatives(booking, item, alternatives);
    } else {
      // Offer different dates
      await this.offerDateAlternatives(booking, item);
    }
  }
}
```

---

**Next:** [Booking Modifications](./BOOKING_ENGINE_05_MODIFICATIONS.md) — Change requests, modifications, and rebooking flows
