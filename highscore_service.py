#!/usr/bin/env python3
"""
Highscore web service for the hexagonal dungeon crawler
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Database setup
DB_PATH = 'highscores.db'

def init_db():
    """Initialize the highscore database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS highscores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            floor_reached INTEGER NOT NULL,
            gold_collected INTEGER NOT NULL,
            enemies_defeated INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/api/submit_score', methods=['POST'])
def submit_score():
    """Submit a new highscore"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'score', 'floor_reached', 'gold_collected', 'enemies_defeated']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Clean username (limit length and remove special chars)
        username = str(data['username']).strip()[:20]
        if not username:
            username = "Anonymous"
        
        # Insert into database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO highscores (username, score, floor_reached, gold_collected, enemies_defeated)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, int(data['score']), int(data['floor_reached']), 
              int(data['gold_collected']), int(data['enemies_defeated'])))
        
        score_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'score_id': score_id,
            'message': 'Score submitted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/highscores', methods=['GET'])
def get_highscores():
    """Get top highscores"""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, score, floor_reached, gold_collected, enemies_defeated, timestamp
            FROM highscores
            ORDER BY score DESC, floor_reached DESC
            LIMIT ?
        ''', (limit,))
        
        scores = []
        for row in cursor.fetchall():
            scores.append({
                'username': row[0],
                'score': row[1],
                'floor_reached': row[2],
                'gold_collected': row[3],
                'enemies_defeated': row[4],
                'timestamp': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'scores': scores,
            'total_count': len(scores)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user_rank', methods=['GET'])
def get_user_rank():
    """Get user's rank and best score"""
    try:
        username = request.args.get('username', '').strip()
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user's best score
        cursor.execute('''
            SELECT score, floor_reached, gold_collected, enemies_defeated, timestamp
            FROM highscores
            WHERE username = ?
            ORDER BY score DESC, floor_reached DESC
            LIMIT 1
        ''', (username,))
        
        user_best = cursor.fetchone()
        if not user_best:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's rank
        cursor.execute('''
            SELECT COUNT(*) + 1 as rank
            FROM highscores
            WHERE score > ? OR (score = ? AND floor_reached > ?)
        ''', (user_best[0], user_best[0], user_best[1]))
        
        rank = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'username': username,
            'best_score': {
                'score': user_best[0],
                'floor_reached': user_best[1],
                'gold_collected': user_best[2],
                'enemies_defeated': user_best[3],
                'timestamp': user_best[4]
            },
            'rank': rank
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get general statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total submissions
        cursor.execute('SELECT COUNT(*) FROM highscores')
        total_submissions = cursor.fetchone()[0]
        
        # Highest score
        cursor.execute('SELECT MAX(score) FROM highscores')
        highest_score = cursor.fetchone()[0] or 0
        
        # Deepest floor
        cursor.execute('SELECT MAX(floor_reached) FROM highscores')
        deepest_floor = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_submissions': total_submissions,
                'highest_score': highest_score,
                'deepest_floor': deepest_floor
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'highscore-service'})

if __name__ == '__main__':
    print("🚀 Starting Highscore Service...")
    init_db()
    print("📊 Database initialized")
    print("🌐 Service running at http://localhost:5000")
    print("📋 Endpoints:")
    print("  POST /api/submit_score - Submit a new score")
    print("  GET  /api/highscores - Get top scores")
    print("  GET  /api/user_rank - Get user rank")
    print("  GET  /api/stats - Get general stats")
    print("  GET  /health - Health check")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
