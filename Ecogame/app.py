from flask import Flask, render_template, request, redirect, url_for, flash
import os
import random 

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_farm_key_for_testing') 

CLIMATE_EFFECTS = {
    'Normal ☀️': {'multiplier': 1.0, 'color': 'info'},
    'Perfect Day 🌈': {'multiplier': 1.25, 'color': 'success'}, # Big boost!
    'Heavy Rain 🌧️': {'multiplier': 0.8, 'color': 'warning'},    # Slight loss
    'Drought 🥵': {'multiplier': 0.5, 'color': 'error'}         # Big loss!
}


LEADERBOARD = [
    {'username': 'EcoMaster', 'points': 2500},
    {'username': 'FarmerGreen', 'points': 1800},
    {'username': 'HappyPlanter', 'points': 1200}
]


SHOP_ITEMS = {
    "bio_fertilizer": {"name": "Bio Fertilizer 🌱", "cost": 100, "health_impact": 15, "info": "The sustainable choice! Boosts health and yield."},
    "chemical_fertilizer": {"name": "Chemical Fertilizer 🧪", "cost": 50, "health_impact": -20, "info": "Cheap, but harms the soil and planet! Avoid this."},
    "irrigation_system": {"name": "Drip System 💧", "cost": 250, "health_impact": 5, "info": "A wise investment for long-term growth and water saving."}
}

CROP_DATA = {
    'wheat': {'name': 'Wheat 🌾', 'base_yield': 100, 'sell_price': 5, 'emoji': '🌾'},
    'rice': {'name': 'Rice 🍚', 'base_yield': 120, 'sell_price': 4, 'emoji': '🍚'}
}

CROP_STAGES = {
    0: {"name": "Empty Field 🚜 - Ready to plant.", "emoji": "🌱"},
    1: {"name": "Seeds Planted 🌱 - Needs water to grow.", "emoji": "🌿"},
    2: {"name": "Growing Fast 📈 - Water again to harvest.", "emoji": "🍃"},
    3: {"name": "Ready to Harvest! 💰 - Go Sell!", "emoji": "⭐"}
}

game_state = {
    'username': '',
    'points': 500,
    'farm_health': 50,
    'inventory': [],
    'crop_chosen': None,      
    'crop_stage': 0,           
    'crop_yield': 0,
    'current_climate': 'Normal ☀️'
}


def update_leaderboard(username, points):
    """Updates the user's score on the global leaderboard."""
    global LEADERBOARD
    
    
    for user in LEADERBOARD:
        if user['username'] == username:
            user['points'] = points
            break
    else:
        
        LEADERBOARD.append({'username': username, 'points': points})
    
    
    LEADERBOARD.sort(key=lambda x: x['points'], reverse=True)



@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            game_state['username'] = username
            return redirect(url_for('farm'))
    return render_template('login.html')

@app.route('/farm')
def farm():
    if not game_state['username']:
        return redirect(url_for('login'))
    
    current_stage = game_state['crop_stage']
    
    
    if current_stage > 0:
        grid_emoji = CROP_STAGES[current_stage]['emoji']
    else:
        grid_emoji = CROP_STAGES[0]['emoji'] # Empty field emoji
        
    game_state['stage_description'] = CROP_STAGES.get(current_stage)['name']

    return render_template('farm.html', state=game_state, grid_emoji=grid_emoji)


@app.route('/select_crops')
def select_crops():
    """Renders the crop selection page if the field is empty."""
    if game_state['crop_chosen']:
        flash(f"⚠️ You already have {game_state['crop_chosen'].capitalize()} planted! Water it or wait to harvest.", 'warning')
        return redirect(url_for('farm'))
    
    
    return render_template('select_crop.html', crops=CROP_DATA, state=game_state)


@app.route('/plant/<crop_type>')
def handle_crop_choice(crop_type):
    """Handles the actual planting choice."""
    if game_state['crop_chosen']:
        return redirect(url_for('farm'))
        
    if crop_type in CROP_DATA:
        game_state['crop_chosen'] = crop_type
        game_state['crop_stage'] = 1 # Stage 1: Planted
        flash(f"✅ You planted **{CROP_DATA[crop_type]['name']}**! Time to water and grow.", 'success')
    else:
        flash("❌ Invalid crop choice.", 'error')
        
    return redirect(url_for('farm'))


@app.route('/advance_day')
def advance_day():
    """Randomly selects a new climate and provides feedback."""
    if not game_state['username']:
        return redirect(url_for('login'))
        
   
    new_climate = random.choice(list(CLIMATE_EFFECTS.keys()))
    game_state['current_climate'] = new_climate
    
    flash(f"🔔 **Day Advanced!** The new weather is **{new_climate}**.", CLIMATE_EFFECTS[new_climate]['color'])
    return redirect(url_for('farm'))


@app.route('/water_grow')
def water_grow():
    """Advances the crop's growth stage and calculates final yield."""
    if not game_state['username']:
        return redirect(url_for('login'))
        
    if game_state['crop_stage'] == 0:
        flash("❌ You need to **Pick Seeds** first! The field is empty.", 'error')
        return redirect(url_for('farm'))

    if game_state['crop_stage'] == 3:
        flash("⚠️ Your crop is already ready to harvest! Go Sell Crops!", 'warning')
        return redirect(url_for('farm'))
    
    game_state['crop_stage'] += 1
    
    if game_state['crop_stage'] == 2:
        flash(f"💧 You watered your {game_state['crop_chosen']}! It's growing bigger.", 'info')
        
    elif game_state['crop_stage'] == 3:
        
        # --- YIELD CALCULATION WITH CLIMATE EFFECT ---
        health_multiplier = game_state['farm_health'] / 100 
        
        climate_key = game_state['current_climate']
        climate_multiplier = CLIMATE_EFFECTS.get(climate_key)['multiplier']
        
        base_yield = CROP_DATA[game_state['crop_chosen']]['base_yield']
        
        # Final yield is affected by both health (sustainability) and climate
        final_yield = int(base_yield * health_multiplier * climate_multiplier)
        game_state['crop_yield'] = final_yield
        
        flash(f"🎉 **HARVEST TIME!** Final yield: {final_yield} units. (Health Multiplier: {health_multiplier:.2f}x, Climate Multiplier: {climate_multiplier:.2f}x). Go sell them!", 'success')
    
    return redirect(url_for('farm'))

@app.route('/sell_crops')
def sell_crops():
    """Calculates points earned and resets the farm."""
    if not game_state['username']:
        return redirect(url_for('login'))
        
    if game_state['crop_stage'] < 3 or game_state['crop_yield'] == 0:
        flash("❌ Nothing to sell yet! Only ready crops can be sold.", 'error')
        return redirect(url_for('farm'))
        
    crop_type = game_state['crop_chosen']
    data = CROP_DATA[crop_type]
    
    total_earnings = game_state['crop_yield'] * data['sell_price']
    game_state['points'] += total_earnings
    
    update_leaderboard(game_state['username'], game_state['points'])
    
    # Reset farm state after harvest
    game_state['crop_chosen'] = None
    game_state['crop_stage'] = 0
    game_state['crop_yield'] = 0
    
    flash(f"💰 You sold your {crop_type.capitalize()} crops for **{total_earnings}** coins! Your farm is now empty and ready for new planting.", 'success')
    return redirect(url_for('farm'))

@app.route('/leaderboard')
def leaderboard():
    """Renders the leaderboard page."""
    if not game_state['username']:
        return redirect(url_for('login'))
    
    return render_template('leaderboard.html', leaderboard=LEADERBOARD, current_user=game_state['username'])

@app.route('/shop')
def shop():
    if not game_state['username']:
        return redirect(url_for('login'))
    return render_template('shop.html', items=SHOP_ITEMS, state=game_state)

@app.route('/buy/<item_id>')
def buy_item(item_id):
    if not game_state['username']:
        return redirect(url_for('login'))
    
    item = SHOP_ITEMS.get(item_id)
    if item:
        if game_state['points'] >= item['cost']:
            game_state['points'] -= item['cost']
            game_state['farm_health'] += item['health_impact']
            game_state['inventory'].append(item['name'])
            game_state['farm_health'] = max(0, min(100, game_state['farm_health']))
            
            if item_id == "chemical_fertilizer":
                flash(f"⚠️ **WARNING!** You bought {item['name']}. Your farm health dropped by 20! Choose Bio-options next time.", 'warning')
            else:
                flash(f"✅ Success! You bought {item['name']}. Points left: {game_state['points']}.", 'success')
        else:
            flash("❌ Not enough coins! Grow more crops or choose cheaper items.", 'error')
    
    return redirect(url_for('shop'))


if __name__ == '__main__':
    app.run(debug=True)