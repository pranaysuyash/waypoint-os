# API Documentation Part 1: OpenAPI Specification

> Complete API specification, schemas, and endpoints

**Series:** API Documentation
**Next:** [Part 2: API Design Guidelines](./API_DOCUMENTATION_02_DESIGN.md)

---

## Table of Contents

1. [OpenAPI 3.1 Specification](#openapi-31-specification)
2. [Authentication](#authentication)
3. [Common Components](#common-components)
4. [Bookings API](#bookings-api)
5. [Payments API](#payments-api)
6. [Search API](#search-api)
7. [Webhooks API](#webhooks-api)

---

## OpenAPI 3.1 Specification

```yaml
# openapi.yaml

openapi: 3.1.0
info:
  title: Travel Agency API
  version: 2.0.0
  description: |
    RESTful API for the Travel Agency platform.

    ## Authentication

    All API requests require authentication using a Bearer token:

    ```
    Authorization: Bearer YOUR_TOKEN
    ```

    ## Rate Limiting

    API requests are rate limited:
    - Free tier: 100 requests/hour
    - Basic tier: 1,000 requests/hour
    - Pro tier: 10,000 requests/hour
    - Enterprise: Custom limits

    Rate limit headers are included in all responses.

  contact:
    name: API Support
    email: api@travelagency.com
    url: https://travelagency.com/support

  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.travelagency.com/v2
    description: Production
  - url: https://staging-api.travelagency.com/v2
    description: Staging
  - url: http://localhost:3000/api/v2
    description: Local development

security:
  - bearerAuth: []

tags:
  - name: Auth
    description: Authentication and authorization
  - name: Bookings
    description: Booking management
  - name: Payments
    description: Payment processing
  - name: Search
    description: Search and discovery
  - name: Webhooks
    description: Webhook management

paths:
  # Auth endpoints
  /auth/register:
    post:
      tag: Auth
      summary: Register new user
      description: Create a new user account
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RegisterRequest'
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          $ref: '#/components/responses/Conflict'

  /auth/login:
    post:
      tag: Auth
      summary: Login user
      description: Authenticate and receive access token
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'

  /auth/refresh:
    post:
      tag: Auth
      summary: Refresh access token
      description: Get a new access token using refresh token
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [refreshToken]
              properties:
                refreshToken:
                  type: string
      responses:
        '200':
          description: Token refreshed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthResponse'

  # Booking endpoints
  /bookings:
    get:
      tag: Bookings
      summary: List bookings
      description: Retrieve a paginated list of bookings
      parameters:
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/Limit'
        - $ref: '#/components/parameters/Sort'
        - in: query
          name: status
          schema:
            type: string
            enum: [pending, confirmed, cancelled, completed]
          description: Filter by status
        - in: query
          name: destination
          schema:
            type: string
          description: Filter by destination
        - in: query
          name: user_id
          schema:
            type: string
            format: uuid
          description: Filter by user (admin only)
      responses:
        '200':
          description: Bookings retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BookingsListResponse'

    post:
      tag: Bookings
      summary: Create booking
      description: Create a new booking
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateBookingRequest'
      responses:
        '201':
          description: Booking created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BookingResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '402':
          $ref: '#/components/responses/PaymentRequired'

  /bookings/{bookingId}:
    parameters:
      - $ref: '#/components/parameters/BookingId'

    get:
      tag: Bookings
      summary: Get booking
      description: Retrieve a single booking by ID
      responses:
        '200':
          description: Booking retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BookingResponse'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'

    patch:
      tag: Bookings
      summary: Update booking
      description: Update booking details (partial update)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateBookingRequest'
      responses:
        '200':
          description: Booking updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BookingResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'

    delete:
      tag: Bookings
      summary: Cancel booking
      description: Cancel a booking
      responses:
        '200':
          description: Booking cancelled
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BookingResponse'
        '404':
          $ref: '#/components/responses/NotFound'
        '409':
          description: Booking cannot be cancelled
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /bookings/{bookingId}/quote:
    parameters:
      - $ref: '#/components/parameters/BookingId'

    get:
      tag: Bookings
      summary: Get booking quote
      description: Retrieve detailed quote for a booking
      responses:
        '200':
          description: Quote retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuoteResponse'

  # Payment endpoints
  /payments/intent:
    post:
      tag: Payments
      summary: Create payment intent
      description: Create a Stripe payment intent for booking payment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreatePaymentIntentRequest'
      responses:
        '201':
          description: Payment intent created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentIntentResponse'

  /payments/{paymentIntent}:
    parameters:
      - in: path
        name: paymentIntent
        required: true
        schema:
          type: string
        description: Payment intent ID

    get:
      tag: Payments
      summary: Get payment intent
      description: Retrieve payment intent details
      responses:
        '200':
          description: Payment intent retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentIntentResponse'

  /payments/{paymentIntent}/confirm:
    parameters:
      - in: path
        name: paymentIntent
        required: true
        schema:
          type: string

    post:
      tag: Payments
      summary: Confirm payment
      description: Confirm and process payment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [payment_method]
              properties:
                payment_method:
                  type: string
                  description: Payment method ID from Stripe
      responses:
        '200':
          description: Payment confirmed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentConfirmationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '402':
          $ref: '#/components/responses/PaymentRequired'

  # Search endpoints
  /search/hotels:
    get:
      tag: Search
      summary: Search hotels
      description: Search for available hotels
      parameters:
        - in: query
          name: destination
          required: true
          schema:
            type: string
          description: City, region, or landmark
          example: Paris
        - in: query
          name: check_in
          required: true
          schema:
            type: string
            format: date
          description: Check-in date (YYYY-MM-DD)
          example: '2025-06-01'
        - in: query
          name: check_out
          required: true
          schema:
            type: string
            format: date
          description: Check-out date (YYYY-MM-DD)
          example: '2025-06-07'
        - in: query
          name: guests
          schema:
            type: integer
            minimum: 1
            maximum: 10
            default: 2
          description: Number of guests
        - in: query
          name: rooms
          schema:
            type: integer
            minimum: 1
            maximum: 10
            default: 1
          description: Number of rooms
        - in: query
          name: min_price
          schema:
            type: number
          description: Minimum price per night
        - in: query
          name: max_price
          schema:
            type: number
          description: Maximum price per night
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/Limit'
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HotelSearchResponse'

  /search/destinations:
    get:
      tag: Search
      summary: Search destinations
      description: Get destination suggestions
      parameters:
        - in: query
          name: q
          required: true
          schema:
            type: string
          description: Search query
          example: Par
        - in: query
          name: limit
          schema:
            type: integer
            minimum: 1
            maximum: 20
            default: 10
          description: Number of results
      responses:
        '200':
          description: Destination suggestions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DestinationSearchResponse'

  # Webhook endpoints
  /webhooks:
    get:
      tag: Webhooks
      summary: List webhooks
      description: List configured webhooks for your account
      responses:
        '200':
          description: Webhooks retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  webhooks:
                    type: array
                    items:
                      $ref: '#/components/schemas/Webhook'

    post:
      tag: Webhooks
      summary: Create webhook
      description: Create a new webhook subscription
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateWebhookRequest'
      responses:
        '201':
          description: Webhook created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Webhook'

  /webhooks/{webhookId}:
    parameters:
      - in: path
        name: webhookId
        required: true
        schema:
          type: string
          format: uuid

    get:
      tag: Webhooks
      summary: Get webhook
      responses:
        '200':
          description: Webhook retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Webhook'

    delete:
      tag: Webhooks
      summary: Delete webhook
      responses:
        '204':
          description: Webhook deleted

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token obtained from /auth/login or /auth/register

  parameters:
    Page:
      in: query
      name: page
      schema:
        type: integer
        minimum: 1
        default: 1
      description: Page number for pagination

    Limit:
      in: query
      name: limit
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
      description: Number of items per page

    Sort:
      in: query
      name: sort
      schema:
        type: string
        enum: [created_at, updated_at, total_price, destination]
        default: created_at
      description: Sort field (prefix with - for descending)

    BookingId:
      in: path
      name: bookingId
      required: true
      schema:
        type: string
        format: uuid
      description: Booking ID

  schemas:
    # Request schemas
    RegisterRequest:
      type: object
      required: [email, password, name]
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          minLength: 8
          description: Must be at least 8 characters
        name:
          type: string
          minLength: 1
        agency_id:
          type: string
          format: uuid
          description: Agency ID (for agents)

    LoginRequest:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
        password:
          type: string

    CreateBookingRequest:
      type: object
      required: [destination, dates, guests]
      properties:
        destination:
          type: string
          description: Destination name or ID
          example: Paris, France
        dates:
          type: object
          required: [start, end]
          properties:
            start:
              type: string
              format: date
              example: '2025-06-01'
            end:
              type: string
              format: date
              example: '2025-06-07'
        guests:
          type: integer
          minimum: 1
          maximum: 20
          example: 2
        services:
          type: array
          items:
            $ref: '#/components/schemas/BookingService'
        customer_notes:
          type: string

    CreatePaymentIntentRequest:
      type: object
      required: [booking_id, amount, currency]
      properties:
        booking_id:
          type: string
          format: uuid
        amount:
          type: integer
          description: Amount in cents
          example: 10000
        currency:
          type: string
          enum: [USD, EUR, GBP, INR, JPY]
          default: USD
        metadata:
          type: object
          description: Additional metadata

    CreateWebhookRequest:
      type: object
      required: [url, events]
      properties:
        url:
          type: string
          format: uri
          description: HTTPS URL to receive webhooks
        events:
          type: array
          items:
            type: string
            enum:
              - booking.created
              - booking.confirmed
              - booking.cancelled
              - payment.succeeded
              - payment.failed
          description: Events to subscribe to
        secret:
          type: string
          description: Webhook signature secret (optional, will be generated)

    # Response schemas
    AuthResponse:
      type: object
      properties:
        access_token:
          type: string
        refresh_token:
          type: string
        token_type:
          type: string
          enum: [Bearer]
        expires_in:
          type: integer
          description: Access token expiry in seconds
        user:
          $ref: '#/components/schemas/User'

    BookingResponse:
      type: object
      properties:
        booking:
          $ref: '#/components/schemas/Booking'

    BookingsListResponse:
      type: object
      properties:
        bookings:
          type: array
          items:
            $ref: '#/components/schemas/Booking'
        pagination:
          $ref: '#/components/schemas/Pagination'

    HotelSearchResponse:
      type: object
      properties:
        hotels:
          type: array
          items:
            $ref: '#/components/schemas/Hotel'
        total:
          type: integer
        pagination:
          $ref: '#/components/schemas/Pagination'

    QuoteResponse:
      type: object
      properties:
        booking:
          $ref: '#/components/schemas/Booking'
        breakdown:
          type: array
          items:
            type: object
            properties:
              category:
                type: string
              description:
                type: string
              amount:
                type: number
              currency:
                type: string
        total:
          type: number
        currency:
          type: string
        valid_until:
          type: string
          format: date-time

    PaymentIntentResponse:
      type: object
      properties:
        id:
          type: string
        client_secret:
          type: string
        amount:
          type: integer
        currency:
          type: string
        status:
          type: string
          enum: [requires_payment_method, processing, requires_action, requires_capture, canceled, succeeded]

    PaymentConfirmationResponse:
      type: object
      properties:
        payment_id:
          type: string
        status:
          type: string
          enum: [succeeded, processing, failed]
        amount:
          type: integer
        currency:
          type: string

    # Common schemas
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        name:
          type: string
        role:
          type: string
          enum: [customer, agent, admin]
        agency_id:
          type: string
          format: uuid
          nullable: true

    Booking:
      type: object
      properties:
        id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        destination:
          type: string
        dates:
          type: object
          properties:
            start:
              type: string
              format: date
            end:
              type: string
              format: date
        guests:
          type: integer
        services:
          type: array
          items:
            $ref: '#/components/schemas/BookingService'
        status:
          type: string
          enum: [pending, confirmed, cancelled, completed]
        total_price:
          type: number
        currency:
          type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    BookingService:
      type: object
      properties:
        type:
          type: string
          enum: [accommodation, transport, activity, insurance]
        details:
          type: object
          additionalProperties: true

    Hotel:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        destination:
          type: string
        address:
          type: string
        rating:
          type: number
          minimum: 0
          maximum: 5
        amenities:
          type: array
          items:
            type: string
        images:
          type: array
          items:
            type: string
            format: uri
        price_per_night:
          type: number
        currency:
          type: string
        availability:
          type: boolean

    Pagination:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer
        total_pages:
          type: integer
        has_next:
          type: boolean
        has_prev:
          type: boolean

    Webhook:
      type: object
      properties:
        id:
          type: string
          format: uuid
        url:
          type: string
          format: uri
        events:
          type: array
          items:
            type: string
        secret:
          type: string
          description: Last 4 characters shown
        active:
          type: boolean
        created_at:
          type: string
          format: date-time

    Error:
      type: object
      properties:
        error:
          type: string
        code:
          type: string
        message:
          type: string
        details:
          type: object
          additionalProperties: true

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error: Bad Request
            code: VALIDATION_ERROR
            message: Validation failed
            details:
              destination: Destination is required

    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error: Unauthorized
            code: INVALID_TOKEN
            message: Invalid or expired token

    Forbidden:
      description: Forbidden
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error: Forbidden
            code: ACCESS_DENIED
            message: You don't have permission to access this resource

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error: Not Found
            code: RESOURCE_NOT_FOUND
            message: The requested resource was not found

    Conflict:
      description: Resource conflict
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error: Conflict
            code: RESOURCE_EXISTS
            message: A resource with this identifier already exists

    PaymentRequired:
      description: Payment required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error: Payment Required
            code: PAYMENT_REQUIRED
            message: Payment is required to complete this request
