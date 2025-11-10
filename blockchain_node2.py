#################################################################
# IMPLÉMENTATION D'UNE BLOCKCHAIN - TP N°1
# Filière: Sciences des Données, Big Data & Intelligence Artificielle
# Basé sur le sujet du Prof. Imad Sassi 
#################################################################

import hashlib
import json
import time
from uuid import uuid4
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

# Difficulté de minage (requis : 4 zéros) 
MINING_DIFFICULTY = "0000"

class Blockchain:
    def __init__(self):
        """
        Constructeur de la classe Blockchain.
        Initialise la chaîne, la liste des transactions courantes,
        l'ensemble des nœuds et crée le bloc genesis.
        """
        self.chain = []
        self.current_transactions = []
        self.nodes = set() # Utilisation d'un set pour l'idempotence [2]

        # Création du bloc genesis (bloc originel)
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Crée un nouveau bloc et l'ajoute à la chaîne.
        :param proof: (int) La preuve de travail fournie
        :param previous_hash: (str) (Optionnel) Hash du bloc précédent
        :return: (dict) Le nouveau bloc
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Réinitialiser la liste des transactions courantes
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Ajoute une nouvelle transaction à la liste des transactions
        qui iront dans le prochain bloc miné.
        :param sender: (str) Adresse de l'expéditeur
        :param recipient: (str) Adresse du destinataire
        :param amount: (int) Montant
        :return: (int) L'index du bloc qui contiendra cette transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Calcule le hash SHA-256 d'un bloc.
        :param block: (dict) Le bloc
        :return: (str) Le hash
        """
        # Il est crucial de trier le dictionnaire (sort_keys=True)
        # pour garantir des hashes déterministes.[3, 4]
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """
        Retourne le dernier bloc de la chaîne.
        """
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Algorithme de Preuve de Travail (Proof of Work) simple :
        - Trouver un nombre 'proof' (nonce) tel que le hash
          (last_proof, proof) commence par MINING_DIFFICULTY (4 zéros).
        :param last_proof: (int) Preuve du bloc précédent
        :return: (int) La nouvelle preuve (nonce)
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Valide si le hash (last_proof, proof) respecte la
        condition de difficulté (commencer par 4 zéros).
        :param last_proof: (int) Preuve précédente
        :param proof: (int) Preuve courante (nonce)
        :return: (bool) True si valide, False sinon.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash.startswith(MINING_DIFFICULTY)

    def is_chain_valid(self, chain):
        """
        Vérifie la validité d'une blockchain donnée.
        Parcourt la chaîne et vérifie deux choses :
        1. L'intégrité des hashes (previous_hash == hash(previous_block))
        2. La validité des preuves de travail (PoW)
        :param chain: (list) Une blockchain
        :return: (bool) True si la chaîne est valide, False sinon.
        """
        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # 1. Vérifier que le hash du bloc précédent est correct
            if block['previous_hash'] != self.hash(previous_block):
                return False

            # 2. Vérifier que la Preuve de Travail est correcte
            if not self.valid_proof(previous_block['proof'], block['proof']):
                return False

            previous_block = block
            current_index += 1

        return True

    def register_node(self, address):
        """
        Ajoute un nouveau nœud à la liste des nœuds du réseau (Partie II).
        :param address: (str) Adresse du nœud (ex: 'http://192.168.0.5:5000')
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepte '192.168.0.5:5000'
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('URL de nœud invalide')

    def resolve_conflicts(self):
        """
        Algorithme de consensus (Partie II).
        Il résout les conflits en remplaçant la chaîne locale par la
        chaîne la plus longue (valide) trouvée sur le réseau.
        C'est la règle de "la chaîne la plus longue".[2, 5]
        :return: (bool) True si la chaîne a été remplacée, False sinon.
        """
        neighbours = self.nodes
        new_chain = None

        # On ne recherche que des chaînes plus longues que la nôtre
        max_length = len(self.chain)

        # Vérifier les chaînes de tous les nœuds de notre réseau
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/get_chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Vérifier si la chaîne est plus longue ET valide
                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        new_chain = chain

            except requests.exceptions.ConnectionError:
                print(f"Échec de la connexion au nœud {node}")

        # Si nous avons trouvé une chaîne valide plus longue, nous remplaçons la nôtre
        if new_chain:
            self.chain = new_chain
            return True

        return False


# --- Initialisation de l'API REST Flask ---

app = Flask(__name__)

# Générer une adresse universellement unique pour ce nœud
node_identifier = str(uuid4()).replace('-', '')

# Instancier la Blockchain
blockchain = Blockchain()


# --- Définition des Endpoints de l'API ---

@app.route('/mine', methods=['GET'])
def mine_block():
    """
    Endpoint de minage (/mine).
    1. Calcule la Preuve de Travail.
    2. Ajoute une transaction de récompense.
    3. Crée le nouveau bloc.
    """
    # 1. Obtenir la preuve de travail
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # 2. Récompenser le mineur 
    # '0' signifie que ce coin est 'miné' (ex nihilo)
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1, # Récompense de 1 unité
    )

    # 3. Forger le nouveau bloc en l'ajoutant à la chaîne
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "Nouveau bloc miné avec succès!",
        'index': block['index'],
        'timestamp': block['timestamp'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200 # 200 OK


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """
    Endpoint de création de transaction (/transactions/new).
    Accepte une transaction au format JSON.
    """
    values = request.get_json()

    # Vérifier que les champs requis sont présents
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Valeurs manquantes', 400 # 400 Bad Request

    # Créer une nouvelle transaction
    index = blockchain.new_transaction(values['sender'],
                                       values['recipient'],
                                       values['amount'])

    response = {'message': f'La transaction sera ajoutée au bloc {index}'}
    return jsonify(response), 201 # 201 Created


@app.route('/get_chain', methods=['GET'])
def get_chain():
    """
    Endpoint de consultation de la chaîne (/get_chain).
    Retourne l'intégralité de la blockchain.
    """
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200 # 200 OK


@app.route('/is_valid', methods=['GET'])
def is_valid():
    """
    Endpoint de validation de la chaîne (/is_valid).
    """
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'La blockchain est valide.'}
    else:
        response = {'message': 'La blockchain n\'est PAS valide.'}
    return jsonify(response), 200 # 200 OK


# --- Endpoints pour la Partie II : Décentralisation ---

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """
    Endpoint d'enregistrement des nœuds (/nodes/register).
    Accepte une liste d'adresses de nœuds au format JSON.
    """
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Erreur : Veuillez fournir une liste valide de nœuds", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Nouveaux nœuds ajoutés avec succès',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201 # 201 Created


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    """
    Endpoint de résolution de consensus (/nodes/resolve).
    Lance l'algorithme de consensus pour résoudre les conflits.
    """
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Notre chaîne a été remplacée par la chaîne faisant autorité.',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Notre chaîne fait autorité.',
            'chain': blockchain.chain
        }
    return jsonify(response), 200 # 200 OK


# --- Démarrage du serveur ---

if __name__ == '__main__':
    # Permet au serveur d'être accessible depuis d'autres machines sur le réseau
    app.run(host='0.0.0.0', port=5001)