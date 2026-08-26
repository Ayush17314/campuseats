# Task 1:

## Pick the partner edge and justify SOAP

### Context

- **Partner:** CampusPay Payment Gateway

- **Operation:** `charge`

- CampusEats integrates with CampusPay to process payments for student food orders.

- SOAP is selected because payment processing requires:
  - A strong WSDL-based contract
  - Standardized fault handling
  - Message-level security
  - Enterprise transaction support

- The formal SOAP contract clearly defines the messages, responses, and errors exchanged between CampusEats and the payment gateway.

- The rest of CampusEats uses REST because normal application APIs can use lightweight HTTP/JSON communication without the additional complexity of SOAP.