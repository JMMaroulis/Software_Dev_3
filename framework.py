import httpcodes
import json
import os
import pickle
import cgi
from flask import Flask, request, render_template, redirect, g, send_from_directory

# Create exportable app
app = Flask(__name__)

# define troop stats
app.troops = {'Augment Gorilla': {'Move': 8, 'Fight': 3, 'Shoot': 0, 'Shield': 10, 'Morale': 2, 'Health': 8, 'Cost': 20,
                                  'Notes': 'Animal, Cannot carry treasure or items'},

              'Lackey': {'Move': 6, 'Fight': 2, 'Shoot': 0, 'Shield': 10, 'Morale': -1, 'Health': 10, 'Cost': 20,
                         'Notes': 'Melee Weapon'},

              'Security': {'Move': 6, 'Fight': 2, 'Shoot': 1, 'Shield': 12, 'Morale': 2, 'Health': 12, 'Cost': 80,
                           'Notes': 'Blaster, Blade'},

              'Engineer': {'Move': 4, 'Fight': 0, 'Shoot': 3, 'Shield': 12, 'Morale': 2, 'Health': 10, 'Cost': 60,
                           'Notes': 'Blaster, Repair Kit'},

              'Medic': {'Move': 5, 'Fight': 0, 'Shoot': 0, 'Shield': 12, 'Morale': 3, 'Health': 10, 'Cost': 50,
                        'Notes': 'Blade, Medkit'},

              'Commando': {'Move': 8, 'Fight': 4, 'Shoot': 0, 'Shield': 10, 'Morale': 4, 'Health': 12, 'Cost': 100,
                           'Notes': 'Stealth Suit, Blade, Needle Gun'},

              'Combat Droid': {'Move': 3, 'Fight': 2, 'Shoot': 4, 'Shield': 14, 'Morale': 0, 'Health': 14, 'Cost': 150,
                               'Notes': 'Mechanoid, Dual Blaster, Claws'}}


# define default captain stats
app.captain = {
    'Captain': {'Move': 5, 'Fight': 2, 'Shoot': 2, 'Shield': 12, 'Morale': 4, 'Health': 12, 'Cost': 0, 'Skillset': [],
                'Specialism': None, 'Items': [], 'Experience': 0}}

# define default ensign stats
app.ensign = {'Ensign': {'Move': 7, 'Fight': 0, 'Shoot': -1, 'Shield': 10, 'Morale': 2, 'Health': 8, 'Skillset': [],
                             'Specialism': None, 'Cost': 250, 'Items': [], 'Experience': 0}}

# specialisms list
app.specialisms = ['Engineering', 'Psychology', 'Marksman', 'Tactics', 'Melee', 'Defence']

# dictionary mapping skills to specialisms
app.skillsets = {'Engineering': ['Repair', 'Sabotage', 'Augment'], 'Psychology': ['Bolster', 'Terror', 'Counter'],
                 'Marksman': ['Aim', 'Pierce', 'Reload'], 'Tactics': ['Squad', 'Ambush', 'Surround'],
                 'Melee': ['Block', 'Risposte', 'Dual'], 'Defence': ['Shield', 'Sacrifice', 'Resolute']}

app.skill_list = ['Repair', 'Sabotage', 'Augment',  'Bolster', 'Terror', 'Counter',
                  'Aim', 'Pierce', 'Reload', 'Squad', 'Ambush', 'Surround',
                  'Block', 'Risposte', 'Dual', 'Shield', 'Sacrifice', 'Resolute']

# available items/cost dictionary
app.weapon = {'Blaster': 5, 'Needle Gun': 12, 'Blade': 3, 'Cannon': 15, 'Whip': 5}

# item costs dictionary
app.cost = {'Blaster': 5, 'Needle Gun': 12, 'Blade': 3, 'Cannon': 15, 'Whip': 5}

app.capweaps = []
app.ensweaps = []


@app.route('/', methods=['GET'])
# runs welcome page
def welcome_page():
    return app.send_static_file('index.html'), httpcodes.OK


# attempts to figure out sum cost of warband
def sumband(createdband):

    total = 0

    # cost for captain items
    for item in createdband['capweap']:
        total = total + app.cost[item]

    # cost for hiring ensign
    if 'Ensign' in createdband.keys():
        total = total + 250

        # cost for ensign items
        for item in createdband['ensweap']:
            total = total + app.cost[item]

    # cost for hired troops
    for troop in createdband['Troops']:
        total = total + app.troops[troop]['Cost']

    print(total)
    return total


# cash validation for new band
def validate_band_cash_new(createdband):
    cash = sumband(createdband)
    #cash = int(request.form['remainingGold'])
    if cash < 0:
        return False
    elif cash >= 0:
        return True


# cash validation for band edit
# NOT CURRENTLY FUNCTIONAL
def validate_band_cash_edit(loadedband, createdband):

    return True

    #it doesn't like calling this, and I'm not sure why
    #cash = createdband['Treasury']
    if cash < 0:
        return False
    elif cash >= 0:
        return True


# troop number validation for new band
def validate_band_troops(createdband):
    if len(createdband['Troops']) > 9:
        return False
    elif len(createdband['Troops']) <= 9:
        return True


# check band name isn't an empty string
def validate_band_name(createdband):
    if not createdband['Name']:
        return False
    elif createdband['Name']:
        return True


# attempts warband creation
@app.route('/new', methods=['GET', 'POST'])
def new_warband():

    # give client new band template
    if request.method == 'GET':
        return render_template('blankband.html', people=app.troops, captain=app.captain, ensign=app.ensign,
                               specs=app.specialisms, skills=app.skillsets, weaps=app.weapon, skill_list=app.skill_list), httpcodes.OK

    # take new band flask form from client
    if request.method == 'POST':

        # pull various details from form
        bandname = request.form['bandname']
        capspec = request.form['capspec']
        capskill = request.form['capskill']
        capweap = json.loads(request.form['capweap'])
        troops = json.loads(request.form['troops'])

        # create dictionary to hold band details
        createdband = dict()

        # define band treasury
        createdband['Treasury'] = int(request.form['remainingGold'])

        # put captain details in band dictionary
        createdband['Name'] = bandname
        createdband['Captain'] = dict(app.captain['Captain'])
        createdband['Captain']['Specialism'] = capspec
        createdband['Captain']['Skillset'].append(capskill)
        createdband['capweap'] = []
        for weapon in capweap:
            createdband['capweap'].append(weapon)

        # if ensign exists, put ensign details in band dictionary
        if 'hasensign' in request.form.keys():

            # pull details from form
            ensspec = request.form['ensspec']
            ensskill = request.form['ensskill']
            print(ensskill)
            ensweap = json.loads(request.form['ensweap'])

            # put details in band dictionary
            createdband['Ensign'] = dict(app.ensign['Ensign'])
            createdband['Ensign']['Specialism'] = ensspec
            createdband['Ensign']['Skillset'].append(ensskill)
            createdband['ensweap'] = []
            for weapon in ensweap:
                createdband['ensweap'].append(weapon)

        # warband name sanitization
        cgi.escape(createdband['Name'])

        # create troop list, populate with troops
        createdband['Troops'] = []
        for item in troops:
            if item != "Empty":
                createdband['Troops'].append(item)

        # too many crew check
        if validate_band_troops(createdband) == False:
            # returns blank, doesn't throw error, doesn't create band
            return render_template('blankband.html', people=app.troops, captain=app.captain, ensign=app.ensign,
                                   specs=app.specialisms, skills=app.skillsets, weaps=app.weapon), httpcodes.BAD_REQUEST

        # not enough money check
        if validate_band_cash_new(createdband) == False:
            return render_template('blankband.html', people=app.troops, captain=app.captain, ensign=app.ensign,
                                   specs=app.specialisms, skills=app.skillsets, weaps=app.weapon), httpcodes.BAD_REQUEST

        # store band details
        pickle.dump(createdband,
                    open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"), bandname),
                         "wb"))

        # create band list
        if os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands")):
            bands = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"))

        # if there are no bands, make a null bands object
        else:
            os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"))
            bands = None

        return render_template('bandlist.html', bands=bands), httpcodes.CREATED


# goes to band roster screen
@app.route('/edit', methods=['GET'])
def edit_warband():
    # create band list
    if os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands")):
        bands = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"))
    # if there are no bands, make null bands object
    else:
        os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"))
        bands = None

    # give client bandlist template
    if request.method == 'GET':
        return render_template('bandlist.html', bands=bands), httpcodes.OK

# goes to edit particular band screen
@app.route('/edit/<band>', methods=['GET', 'POST'])
def edit_given_warband(band):
    loadedband = pickle.load(
        open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"), band), "rb"))

    # gives client warband details and editband template
    if request.method == 'GET':
        return render_template('editband.html', band=loadedband, people=app.troops, captain=app.captain,
                               ensign=app.ensign, specs=app.specialisms, skills=app.skillsets,
                               weaps=app.weapon, capweaps=loadedband['capweap']), httpcodes.OK

    # takes flask form containing warband details from client
    if request.method == 'POST':

        # pulls various details from form
        bandname = request.form['bandname']
        capspec = request.form['capspec']
        capweap = json.loads(request.form['capweap'])
        skills = json.loads(request.form['capskill'])
        capweap = json.loads(request.form['capweap'])
        troops = json.loads(request.form['troops'])

        # pull captain stats
        captain_move = request.form['capmove']
        captain_fight = request.form['capfight']
        captain_shoot = request.form['capshoot']
        captain_shield = request.form['capshield']
        captain_morale = request.form['capmorale']
        captain_health = request.form['caphealth']
        captain_experience = request.form['capexperience']

        # create band dictionary for warband detail storage
        createdband = dict()

        # store details in dictionary
        createdband['Name'] = bandname
        createdband['Captain'] = dict(app.captain['Captain'])
        createdband['Captain']['Specialism'] = capspec
        createdband['Captain']['Skillset'].extend(skills)
        createdband['Captain']['Items'].append(capweap)
        createdband['Captain']['Move'] = captain_move
        createdband['Captain']['Fight'] = captain_fight
        createdband['Captain']['Shoot'] = captain_shoot
        createdband['Captain']['Shield'] = captain_shield
        createdband['Captain']['Morale'] = captain_morale
        createdband['Captain']['Health'] = captain_health
        createdband['Captain']['Experience'] = captain_experience
        createdband['capweap'] = []
        for weapon in capweap:
            createdband['capweap'].append(weapon)



        # if ensign exists, pull ensign stats
        if 'hasensign' in request.form.keys():

            ensspec = request.form['ensspec']
            #ensign skills proving difficult, using empty placeholder for now
            #ensskill = request.form['ensskill']
            #ensign_skill = json.loads(request.form['ensign_skill'])
            ensign_skill = []
            ensign_move = request.form['ensmove']
            ensign_fight = request.form['ensfight']
            ensign_shoot = request.form['ensshoot']
            ensign_shield = request.form['ensshield']
            ensign_morale = request.form['ensmorale']
            ensign_health = request.form['enshealth']
            ensign_experience = request.form['ensexperience']
            ensweap = json.loads(request.form['ensweap'])

            createdband['Ensign'] = dict(app.ensign['Ensign'])
            createdband['Ensign']['Specialism'] = ensspec
            createdband['Ensign']['Skillset'].extend(ensign_skill)
            createdband['Ensign']['Items'].append(ensweap)
            createdband['Ensign']['Move'] = ensign_move
            createdband['Ensign']['Fight'] = ensign_fight
            createdband['Ensign']['Shoot'] = ensign_shoot
            createdband['Ensign']['Shield'] = ensign_shield
            createdband['Ensign']['Morale'] = ensign_morale
            createdband['Ensign']['Health'] = ensign_health
            createdband['Ensign']['Experience'] = ensign_experience
            createdband['ensweap'] = []
            for weapon in ensweap:
                createdband['ensweap'].append(weapon)

        # warband name sanitisation
        cgi.escape(createdband['Name'])

        # create troops list
        createdband['Troops'] = []

        # populate troop list
        for troop in troops:
            if troop != "Empty":
                createdband['Troops'].append(troop)

        # troop number validation
        if not validate_band_troops(createdband):
            print('troop valid fail')
            return render_template('editband.html', band=loadedband, people=app.troops, captain=app.captain,
                                   ensign=app.ensign, specs=app.specialisms, skills=app.skillsets,
                                   weaps=app.weapon), httpcodes.BADREQUEST

        # warband cash validation
        # method not currently funcitonal, always returns true
        if not validate_band_cash_edit(loadedband, createdband):
            print('cash valid fail')
            return render_template('editband.html', band=loadedband, people=app.troops, captain=app.captain,
                                   ensign=app.ensign, specs=app.specialisms, skills=app.skillsets,
                                   weaps=app.weapon), httpcodes.BADREQUEST

        # warband name validation
        if not validate_band_name(createdband):
            print('name valid fail')
            return render_template('editband.html', band=loadedband, people=app.troops, captain=app.captain,
                                   ensign=app.ensign, specs=app.specialisms, skills=app.skillsets,
                                   weaps=app.weapon), httpcodes.BADREQUEST

        # at this point, have passed validation

        # delete original if name changes
        # FOR THE LOVE OF ALL THAT'S HOLY, DO THIS AFTER THE VALIDATION
        # DELETING THINGS IS BAD
        if loadedband['Name'] != bandname:
            delete_given_warband(loadedband['Name'])
            print('Deleting duplicate!')

        # set treasury from form
        createdband['Treasury'] = int(request.form['remainingGold'])

        # store details
        pickle.dump(createdband,
                    open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"), bandname),
                         "wb"))

        # re-render edit band screen with made changes
        return render_template('editband.html', band=createdband, people=app.troops, captain=app.captain,
                               ensign=app.ensign, specs=app.specialisms, skills=app.skillsets,
                               weaps=app.weapon), httpcodes.OK


@app.route('/delete/<band>', methods=['GET'])
def delete_given_warband(band):
    # deletes band file
    os.remove(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands", band))

    # create band list
    if os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands")):
        bands = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"))

    # if there are no bands, make a null bands object
    else:
        os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "bands"))
        bands = None

    if request.method == 'GET':
        return render_template('bandlist.html', bands=bands), httpcodes.OK


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
