import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Test that the main page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Smart Election Navigator' in response.data


def test_chat_api_missing_message(client):
    """Test the chat API returns 400 if message body is empty."""
    response = client.post('/api/chat', json={})
    assert response.status_code == 400


def test_chat_api_empty_string(client):
    """Test the chat API returns 400 if message is an empty string."""
    response = client.post('/api/chat', json={'message': '   '})
    assert response.status_code == 400


def test_chat_api_message_too_long(client):
    """Test the chat API returns 400 if message exceeds 1000 characters."""
    response = client.post('/api/chat', json={'message': 'a' * 1001})
    assert response.status_code == 400


def test_chat_api_response_format(client):
    """Test the chat API returns a 'response' key (may use fallback without API key)."""
    response = client.post('/api/chat', json={
        'message': 'How do I register to vote in India?',
        'language': 'English',
        'context': 'General Voter'
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'response' in json_data
    assert isinstance(json_data['response'], str)
    assert len(json_data['response']) > 0


def test_chat_api_persona_context(client):
    """Test the chat API accepts and processes different personas."""
    for persona in ['First-Time Voter', 'Overseas/Absentee Voter', 'Accessibility Needs', 'General Voter']:
        response = client.post('/api/chat', json={
            'message': 'How do I vote?',
            'language': 'English',
            'context': persona
        })
        assert response.status_code == 200
        assert 'response' in response.get_json()


def test_404_handler(client):
    """Test that unknown routes return a JSON 404."""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
