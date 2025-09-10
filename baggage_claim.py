import logging
from typing import Dict, Any, List
from http import HTTPStatus
from enum import Enum

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class SupportedFunctions(Enum):
    """Enumeration of supported function names"""
    FIND_BAGGAGE = 'find_baggage'
    CHECK_FLIGHT_STATUS = 'check_flight_status'
    BOOK_FLIGHT = 'book_flight'
    CANCEL_RESERVATION = 'cancel_reservation'

def extract_parameters(parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract parameters from Bedrock agent event format"""
    if not isinstance(parameters, list):
        return {}
    
    result = {}
    for item in parameters:
        if isinstance(item, dict) and 'name' in item and 'value' in item:
            result[item['name']] = item['value']
    
    return result

def validate_required_params(params: Dict[str, Any], required: List[str]) -> None:
    """Validate that all required parameters are present"""
    missing = [param for param in required if not params.get(param)]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")

def create_response(action_group: str, function: str, body: str) -> Dict[str, Any]:
    """Create a standardized response for Bedrock agent"""
    return {
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': body
                    }
                }
            }
        },
        'messageVersion': 1
    }

def find_baggage(flight_number: str, phone_number: str) -> str:
    """Find baggage information for a flight and phone number"""
    logger.info(f"Searching for baggage on flight {flight_number} for phone {phone_number}")
    
    # Mock response for demo
    return f"Found baggage information for flight {flight_number}. " \
           f"Your baggage is currently at baggage claim area B. " \
           f"Contact number on file: {phone_number}"

def check_flight_status(flight_number: str) -> str:
    """Check the status of a flight"""
    logger.info(f"Checking status for flight {flight_number}")
    
    # Mock response for demo
    return f"Flight {flight_number} is currently on time. " \
           f"Departure: 3:30 PM, Arrival: 6:45 PM, Gate: A12"

def book_flight(departure_city: str, arrival_city: str, departure_date: str, 
                passenger_name: str, phone_number: str) -> str:
    """Book a flight reservation"""
    logger.info(f"Booking flight from {departure_city} to {arrival_city} for {passenger_name}")
    
    # Mock response for demo
    confirmation_code = "ABC123"
    return f"Flight booked successfully! " \
           f"Confirmation code: {confirmation_code}. " \
           f"Route: {departure_city} to {arrival_city} on {departure_date}. " \
           f"Passenger: {passenger_name}, Contact: {phone_number}"

def cancel_reservation(confirmation_code: str, phone_number: str) -> str:
    """Cancel a flight reservation"""
    logger.info(f"Canceling reservation {confirmation_code} for phone {phone_number}")
    
    # Mock response for demo
    return f"Reservation {confirmation_code} has been successfully canceled. " \
           f"Refund will be processed to the original payment method within 3-5 business days."

def route_function_call(function_name: str, params: Dict[str, Any]) -> str:
    """Route function call to appropriate handler"""
    
    if function_name == SupportedFunctions.FIND_BAGGAGE.value:
        validate_required_params(params, ['phoneNumber', 'flightNumber'])
        return find_baggage(params['flightNumber'], params['phoneNumber'])
    
    elif function_name == SupportedFunctions.CHECK_FLIGHT_STATUS.value:
        validate_required_params(params, ['flightNumber'])
        return check_flight_status(params['flightNumber'])
    
    elif function_name == SupportedFunctions.BOOK_FLIGHT.value:
        validate_required_params(params, ['departureCity', 'arrivalCity', 'departureDate', 
                                        'passengerName', 'phoneNumber'])
        return book_flight(
            params['departureCity'], params['arrivalCity'], params['departureDate'],
            params['passengerName'], params['phoneNumber']
        )
    
    elif function_name == SupportedFunctions.CANCEL_RESERVATION.value:
        validate_required_params(params, ['confirmationCode', 'phoneNumber'])
        return cancel_reservation(params['confirmationCode'], params['phoneNumber'])
    
    else:
        supported = [func.value for func in SupportedFunctions]
        raise ValueError(f"Unsupported function: {function_name}. Supported: {', '.join(supported)}")

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for Bedrock agent function calls"""
    
    try:
        # Extract event data
        action_group = event['actionGroup']
        function_name = event['function']
        parameters = event.get('parameters', [])
        agent = event['agent']
        
        logger.info(f"Processing function '{function_name}' from action group '{action_group}'")
        
        # Extract and validate parameters
        params = extract_parameters(parameters)
        logger.info(f"Extracted parameters: {list(params.keys())}")
        
        # Route to appropriate function and get result
        result_body = route_function_call(function_name, params)
        
        # Build and return response
        response = create_response(action_group, function_name, result_body)
        logger.info('Successfully processed function call')
        return response
        
    except KeyError as e:
        logger.error(f"Missing required field: {str(e)}")
        error_msg = f"Missing required field: {str(e)}. Please contact IT support."
        
        return create_response(
            event.get('actionGroup', 'unknown'),
            event.get('function', 'unknown'), 
            error_msg
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        error_msg = f"Validation error: {str(e)}. Please check your input and try again."
        
        return create_response(
            event.get('actionGroup', 'unknown'),
            event.get('function', 'unknown'),
            error_msg
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        error_msg = "An unexpected error occurred. Please contact IT support."
        
        return create_response(
            event.get('actionGroup', 'unknown'),
            event.get('function', 'unknown'),
            error_msg
        )