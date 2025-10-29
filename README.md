# Solar Energy Corporation - Inventory & Operations Management System

As the Backend Developer for a large solar energy corporation,
I designed and built a comprehensive Inventory and Operations Management System using Django REST Framework.
This centralized platform was critical for tracking the company's assets across multiple selling points, storage repositories, and workshops.

The system provided role-based dashboards and APIs for managers at all levels.
It enabled precise tracking of every solar component—from its origin in a repository to its final use in a workshop installation,
a cash sale, or a specific project. The platform featured complete historical traceability, 
allowing users to audit the entire lifecycle of any product and review all actions performed by any user on a given date, ensuring full accountability and operational clarity.

## Key Features

- **Centralized Inventory Management**: Track solar components across multiple repositories and workshops
- **Role-Based Access Control**: Different dashboards and permissions for managers, repository staff, and workshop technicians
- **Complete Asset Traceability**: Follow every component from origin to final deployment
- **Historical Audit System**: Comprehensive logging of all user actions and inventory changes
- **Real-time Inventory Updates**: Live tracking of stock levels across all locations

## Technical Implementation

### Core API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/account/token/` | POST | User authentication and token generation |
| `/home/` | GET | Overview of products across repositories (amounts, categories, names) |
| `/add_product/` | POST | Add new product to specific repository |
| `/reserve/` | POST | Reserve specific product amount from specific repository |
| `/Workshop_details/` | GET | Detailed information about workshop operations and inventory |

### System Architecture

- **Multi-location Inventory**: Track components across repositories, workshops, and selling points
- **Lifecycle Management**: Monitor products from acquisition to deployment/sale
- **Audit Trail**: Complete historical record of all inventory movements and user actions
- **Role-Based Dashboards**: Tailored interfaces for different user types and responsibilities

## Technology Stack

- **Backend Framework**: Django + Django REST Framework
- **Authentication**: Token-based authentication with role-based permissions
- **Database**: PostgreSQL (enterprise-grade for complex relationships and audit trails)
- **API Design**: RESTful architecture with comprehensive error handling

## Business Impact

This system transformed the corporation's operations by:
- Eliminating manual inventory tracking across multiple locations
- Providing real-time visibility into stock levels and component movement
- Enabling precise auditing and accountability for all inventory actions
- Reducing operational errors and improving resource allocation

## Setup & Installation

```bash
# Installation steps
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
