import streamlit as st
import json
import random
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from uuid import uuid4

# Initialize session state
if 'player' not in st.session_state:
    st.session_state.player = None
    st.session_state.day = 1

# Data storage setup
USERS_DIR = Path('users')
USERS_DIR.mkdir(exist_ok=True)

class Tree:
    def __init__(self, species: str, position: Tuple[int, int]):
        self.species = species
        self.planted_on = 0
        self.growth_stage = "seedling"
        self.position = position

    def to_dict(self):
        return {
            'species': self.species,
            'planted_on': self.planted_on,
            'growth_stage': self.growth_stage,
            'position': self.position
        }

class ActionLog:
    def __init__(self, day: int, action_type: str, result: str):
        self.day = day
        self.action_type = action_type
        self.result = result

    def to_dict(self):
        return {
            'day': self.day,
            'action_type': self.action_type,
            'result': self.result
        }

class Land:
    CLIMATE_PROBABILITIES = {'sunny': 0.5, 'rain': 0.3, 'drought': 0.2}
    
    def __init__(self, size: int = 5):
        self.soil_health = 20
        self.water_level = 30
        self.fertility = 20
        self.trees: List[Tree] = []
        self.elevation_map = [[random.randint(1, 5) for _ in range(size)] for _ in range(size)]
        self.specimens: Dict[str, List[Tuple[int, int]]] = {}
        self.spring_status = "dry"
        self.appearance = "degraded"
        self.day = 1
        self.climate = "sunny"
        self.spring_active_days = 0

    def generate_climate(self):
        climates = list(self.CLIMATE_PROBABILITIES.keys())
        weights = list(self.CLIMATE_PROBABILITIES.values())
        self.climate = random.choices(climates, weights=weights, k=1)[0]

    def check_spring_activation(self):
        if (self.soil_health >= 90 and self.water_level >= 90 
            and self.fertility >= 90 and len([t for t in self.trees if t.growth_stage == "mature"]) >= 5):
            if self.spring_status == "dry":
                self.spring_status = "forming"
            elif self.spring_status == "forming":
                self.spring_status = "active"
        else:
            self.spring_status = "dry"

    def to_dict(self):
        return {
            'soil_health': self.soil_health,
            'water_level': self.water_level,
            'fertility': self.fertility,
            'trees': [t.to_dict() for t in self.trees],
            'elevation_map': self.elevation_map,
            'specimens': {k: [list(p) for p in v] for k, v in self.specimens.items()},
            'spring_status': self.spring_status,
            'appearance': self.appearance,
            'day': self.day,
            'climate': self.climate,
            'spring_active_days': self.spring_active_days
        }

class Player:
    def __init__(self, name: str):
        self.id = str(uuid4())
        self.name = name
        self.land = Land()
        self.history: List[ActionLog] = []

    def log_action(self, action_type: str, result: str):
        self.history.append(ActionLog(self.land.day, action_type, result))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'land': self.land.to_dict(),
            'history': [h.to_dict() for h in self.history]
        }

def create_user(username):
    player = Player(username)
    save_player(player)
    return player

def save_player(player: Player):
    with open(USERS_DIR / f'{player.id}.json', 'w') as f:
        json.dump(player.to_dict(), f)

def load_player(player_id):
    with open(USERS_DIR / f'{player_id}.json', 'r') as f:
        player_data = json.load(f)
    player = Player(player_data['name'])
    player.id = player_data['id']
    player.land.soil_health = player_data['land']['soil_health']
    player.land.water_level = player_data['land']['water_level']
    player.land.fertility = player_data['land']['fertility']
    player.land.trees = [Tree(t['species'], t['position']) for t in player_data['land']['trees']]
    player.land.elevation_map = player_data['land']['elevation_map']
    player.land.specimens = player_data['land']['specimens']
    player.land.spring_status = player_data['land']['spring_status']
    player.land.appearance = player_data['land']['appearance']
    player.land.day = player_data['land']['day']
    player.land.climate = player_data['land']['climate']
    player.land.spring_active_days = player_data['land']['spring_active_days']
    player.history = [ActionLog(h['day'], h['action_type'], h['result']) for h in player_data['history']]
    return player

def plant_tree(player: Player):
    species_options = ['Ipê Amarelo', 'Pau-Brasil', 'Jequitibá', 'Araucária']
    species = random.choice(species_options)
    
    x = random.randint(0, len(player.land.elevation_map)-1)
    y = random.randint(0, len(player.land.elevation_map)-1)
    
    if player.land.climate == "drought":
        player.log_action("plant", "Plantio falhou devido à seca")
        return " Seca extrema - plantio não realizado"
    
    new_tree = Tree(species, (x, y))
    player.land.trees.append(new_tree)
    
    if species not in player.land.specimens:
        player.land.specimens[species] = []
    player.land.specimens[species].append((x, y))
    
    player.land.soil_health = min(100, player.land.soil_health + 2)
    player.land.fertility = min(100, player.land.fertility + 1)
    player.log_action("plant", f"Plantou {species} em ({x},{y})")
    return f" {species} plantada com sucesso!"

def irrigate(player: Player):
    if player.land.climate == "rain":
        player.log_action("irrigate", "Irrigação natural pela chuva")
        return " Chuva natural aumenta umidade"
    
    player.land.water_level = min(100, player.land.water_level + 15)
    player.land.soil_health = min(100, player.land.soil_health + 3)
    player.log_action("irrigate", "Terreno irrigado")
    return " Irrigação realizada com sucesso"

def regenerate_soil(player: Player):
    player.land.fertility = min(100, player.land.fertility + 8)
    player.land.soil_health = min(100, player.land.soil_health + 5)
    player.land.water_level = max(0, player.land.water_level - 10)
    player.log_action("regenerate", "Solo regenerado")
    return " Solo regenerado com nutrientes"

def advance_day(player: Player):
    # Update tree growth
    for tree in player.land.trees:
        tree.planted_on += 1
        if tree.planted_on > 5:
            tree.growth_stage = "young"
        elif tree.planted_on > 10:
            tree.growth_stage = "mature"
    
    # Apply climate effects
    prev_climate = player.land.climate
    player.land.generate_climate()
    
    if player.land.climate == "rain":
        player.land.water_level = min(100, player.land.water_level + 20)
    elif player.land.climate == "drought":
        player.land.water_level = max(0, player.land.water_level - 25)
    
    # Update spring status
    player.land.check_spring_activation()
    
    # Track consecutive active days
    if player.land.spring_status == "active":
        player.land.spring_active_days += 1
    else:
        player.land.spring_active_days = 0
    
    player.land.day += 1
    save_player(player)

def check_victory(player: Player):
    return player.land.spring_active_days >= 3

def show_elevation_map(land):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_title('Mapa de Elevação do Terreno')
    im = ax.imshow(land.elevation_map, cmap='terrain')
    plt.colorbar(im, ax=ax)
    st.pyplot(fig)

def show_victory_progress(player):
    st.subheader("Progresso para o Novo Rio")
    col1, col2, col3 = st.columns(3)
    col1.metric("Saúde do Solo", f"{player.land.soil_health}%")
    col2.metric("Nível de Água", f"{player.land.water_level}%")
    col3.metric("Fertilidade", f"{player.land.fertility}%")
    
    st.progress(player.land.spring_active_days/3, 
               text=f"Dias consecutivos com nascente ativa: {player.land.spring_active_days}/3")
    
    if player.land.spring_status != "dry":
        st.success(f" Status da Nascente: {player.land.spring_status.upper()}")

def show_terrain_feedback(player):
    feedback = []
    land = player.land
    
    if land.spring_status == "active":
        feedback.append(" Você ouve o som de água corrente!")
    if land.trees:
        mature_trees = len([t for t in land.trees if t.growth_stage == "mature"])
        feedback.append(f" Árvores maduras: {mature_trees}")
    if land.climate == "drought":
        feedback.append(" Alerta de seca!")
    
    if feedback:
        st.subheader("Observações do Terreno")
        for msg in feedback:
            st.markdown(f"- {msg}")

# Streamlit UI
st.title(' Novo Rio - Jogo de Reflorestamento')

# User creation
with st.sidebar:
    st.header('Jogador')
    username = st.text_input('Nome do Jogador')
    if st.button('Criar Novo Jogador') and username:
        player = create_user(username)
        st.session_state.player = player
        st.rerun()

if st.session_state.player:
    player = st.session_state.player
    
    if check_victory(player):
        st.balloons()
        st.success(" PARABÉNS! Você restaurou o curso do rio!")
        st.image("https://cdn.pixabay.com/photo/2017/09/01/13/56/river-2704097_1280.jpg")
        st.stop()
    
    st.header(f"Terreno de {player.name} - Dia {player.land.day}")
    st.subheader(f"Clima Atual: {player.land.climate.title()}️")
    
    show_victory_progress(player)
    show_terrain_feedback(player)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(' Plantar Árvore'):
            result = plant_tree(player)
            st.toast(result)
            advance_day(player)
            st.rerun()
    
    with col2:
        if st.button(' Irrigar'):
            result = irrigate(player)
            st.toast(result)
            advance_day(player)
            st.rerun()
    
    with col3:
        if st.button(' Regenerar Solo'):
            result = regenerate_soil(player)
            st.toast(result)
            advance_day(player)
            st.rerun()
    
    with st.expander("Mapa do Terreno"):
        show_elevation_map(player.land)
    
    with st.expander("Histórico de Ações"):
        for log in reversed(player.history[-5:]):
            st.markdown(f"**Dia {log.day}**: {log.result}")
    
    if st.button(' Avançar para o próximo dia'):
        advance_day(player)
        st.rerun()
else:
    st.info(' Crie um jogador para começar')
