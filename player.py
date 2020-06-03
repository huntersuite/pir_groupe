import numpy as np
import os
from numpy.random import randint

class Player:

    def __init__(self):
        self.dt = 0.5
        self.efficiency=0.95
        self.sun=[]
        self.bill = np.zeros(48) # prix de vente de l'électricité
        self.load= np.zeros(48) # chargement de la batterie (li)
        self.penalty=np.zeros(48)
        self.grid_relative_load=np.zeros(48)
        self.battery_stock = np.zeros(49) #a(t)
        self.capacity = 100
        self.max_load = 70
        self.prices = {"purchase" : [],"sale" : []}
        self.imbalance={"purchase_cover":[], "sale_cover": []}
        # ATTENTION ON A RAJOUTE DEUX VARIABLES A SELF 
        self.memoire_NRJ = 0
        self.memoire_prix_interne = np.zeros(48)

    def take_decision(self, time):
        #ON A AJOUTE self.memoire_NRJ = 0 
        # et self.memoire_prix_interne = np.zeros(48)
        #DANS _INIT_. 
        #FAITES ATTENTION SI VOUS COPIEZ DES PARTIES DU CODE, MERCI !
        
        duree_pas_de_temps = self.dt
        chargement_batterie = 0
        
        moyenne_prix_journee = 0
        for temps in range (14,37):
            moyenne_prix_journee += self.memoire_prix_interne[temps]
        moyenne_prix_journee = moyenne_prix_journee/22 
        
        nombre_de_pas_ou_le_dechargement_est_prioritaire = 10
        if (time == 40):
            self.memoire_NRJ = self.battery_stock[39] / nombre_de_pas_ou_le_dechargement_est_prioritaire 

        NRJ = self.memoire_NRJ 
        if (NRJ > self.max_load * duree_pas_de_temps):
            cas = 1  # batterie chargee a bloc
            NRJ_restante = nombre_de_pas_ou_le_dechargement_est_prioritaire *(NRJ - self.max_load * duree_pas_de_temps) 
            # pour decharger la nuit
        else:
            cas = 2  # batterie pas chargee a fond

        if time >= 20 and time < 36:  # chargement de la batterie au milieu de la journee
            if (self.memoire_prix_interne[time] < 0.9*moyenne_prix_journee):
                chargement_batterie = (self.sun[time - 1]* 3 / 5)  
            else : 
                chargement_batterie = 0
            
            if (self.battery_stock[
                    time - 1] + chargement_batterie * duree_pas_de_temps) > self.capacity:  # verification de la capacite
                chargement_batterie = np.maximum((self.capacity - self.battery_stock[time - 1]) / duree_pas_de_temps, 0) 

        elif (time >= 12) and (time <= 15):  # dechargement le matin (heure de pointe)
            if (cas == 2):
                chargement_batterie = - NRJ / duree_pas_de_temps
            else:
                chargement_batterie = - self.max_load

        elif ((time >= 40) and (time <= 43)):  # dechargement le soir (heure de pointe)
            if (cas == 2):
                chargement_batterie = - NRJ / duree_pas_de_temps
            else:
                chargement_batterie = - self.max_load

        elif (((time < 12) or (43 < time)) and (time > 0)):  # dechargement du reste de la batterie la nuit
            if (cas == 1):
                chargement_batterie = - NRJ_restante / duree_pas_de_temps / (12 + 5)
                # 5 correspond au nombre de pas de temps entre 22H et minuit ???
            else:
                chargement_batterie = 0
                
        # On cherche à voir si c'est interessant de décharger la nuit 
        # Il faudrait tester si 
        # Memoire_bonus + memoire_prix * chargement_batterie  > ( memoire_prix * chargement_batterie )sur 8 pas de temps  
        elif(time ==0):
            chargement_batterie = - 2 * NRJ / duree_pas_de_temps
            
        # Enregistrement du prix 
        if (time == 0):
            self.memoire_prix_interne[47] = 0 
            # on aimerait bien self.prices["sale"][47] mais au premier jour de la simulation ça ne passe pas
            # Solution possible : faire un compteur pour les jours 
            # Mais flemme parce que de toute façon on ne se sert pas du prix à minuit 
        else:
            self.memoire_prix_interne[time-1] = self.prices["sale"][time-1]
        
        # On vérifie qu'on ne dépasse pas la puissance max.
        if (abs(chargement_batterie) > self.max_load):
            chargement_batterie = self.max_load * np.sign(chargement_batterie)
        return chargement_batterie

    def update_battery_stock(self, time,load):
        if abs(load) > self.max_load:
            load = self.max_load*np.sign(load) #saturation au maximum de la batterie
        new_stock = self.battery_stock[time] + (self.efficiency*max(0,load) - 1/self.efficiency * max(0,-load))*self.dt
            
            #On rétablit les conditions si le joueur ne les respecte pas :
            
        if new_stock < 0: #impossible, le min est 0, on calcule le load correspondant
            load = - self.battery_stock[time] / (self.efficiency*self.dt)
            new_stock = 0
        elif new_stock > self.capacity:
            load = (self.capacity - self.battery_stock[time]) / (self.efficiency*self.dt)
            new_stock = self.capacity
        
        self.battery_stock[time+1] = new_stock
        return load
        
    def compute_load(self,time,sun):
        load_player = self.take_decision(time)
        load_battery=self.update_battery_stock(time,load_player)
        self.load[time]=load_battery - sun
        
        return self.load[time]
    
    def observe(self, t, sun, price, imbalance,grid_relative_load):
        self.sun.append(sun)
        
        self.prices["purchase"].append(price["purchase"])
        self.prices["sale"].append(price["sale"])

        self.imbalance["purchase_cover"].append(imbalance["purchase_cover"])
        self.imbalance["sale_cover"].append(imbalance["sale_cover"])
        self.grid_relative_load[t]=grid_relative_load
    
    def reset(self):
        self.load= np.zeros(48)
        self.bill = np.zeros(48)
        self.penalty=np.zeros(48)
        self.grid_relative_load=np.zeros(48)
        
        last_bat = self.battery_stock[-1]
        self.battery_stock = np.zeros(49)
        self.battery_stock[0] = last_bat
        
        self.sun=[]
        self.prices = {"purchase" : [],"sale" : []}
        self.imbalance={"purchase_cover":[], "sale_cover": []}
