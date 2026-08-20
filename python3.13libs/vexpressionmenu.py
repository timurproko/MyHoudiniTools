from builtins import zip
import hou
import snippetmenu
import re

_hasloadedsnippets = False

_initialsnippets = {}
_vexsnippets = {}
_vexsnippets_sol = {}

_initialsnippets['agentcliplayer/localexpression'] = [
"""blendratio = blendratio;
weight = weight;

overrideclipspeed = overrideclipspeed;
clipspeedmultiplier = clipspeedmultiplier;
overridelocomotionspeed = overridelocomotionspeed;
locomotionspeedmultiplier = locomotionspeedmultiplier;

randomizeclipspeed = randomizeclipspeed;
clipspeedvariance = clipspeedvariance;
clipspeedseed = clipspeedseed;

setinitialcliptime = setinitialcliptime;
initialcliptime = initialcliptime;

randomizecliptime = randomizecliptime;
randomclipoffset = randomclipoffset;
randomclipoffsetseed = randomclipoffsetseed;""",
    'Pass Through',
]

_initialsnippets['agentcliplayer/localweightexpression'] = [
"""blendratios = blendratios;
weights = weights;""",
    'Pass Through',
]

_initialsnippets['crowdstate::3.0/localexpression'] = [
"""clipspeedmultiplier = clipspeedmultiplier;
locomotionspeedmultiplier = locomotionspeedmultiplier;

randomizeclipspeed = randomizeclipspeed;
clipspeedvariance = clipspeedvariance;
clipspeedseed = clipspeedseed;""",
    'Pass Through',
]

_initialsnippets['crowdtransition::3.0/localexpression'] = [
"""instate = instate;
outstate = outstate;
useoutclip = useoutclip;
outclip = outclip;""",
    'Pass Through',
]

_initialsnippets['popforce/localforceexpression'] = [
    "force = force;",
        'Pass Through',
]

_initialsnippets['popforce/localnoiseexpression'] = [
"""amp = amp;
rough = rough;
atten = atten;
turb = turb;
pulselength = pulselength;
swirlscale = swirlscale;
swirlsize = swirlsize;
offset = offset;""",
    'Pass Through',
    "amp *= rand(@id);",
    'Randomize Amplitude',
]

_initialsnippets['popattract/primuvcode'] = [
"""goalprim = goalprim;
goalprimuv = goalprimuv;""",
    'Pass Through',
    "goalprimuv.x = @nage;",
    'Follow Curve by Normalized Age',
]

_initialsnippets['popattract/goalcode'] = [
"""goal = goal;
goalvel = goalvel;""",
    'Pass Through',
]

_initialsnippets['popattract/forcecode'] = [
"""forcemethod = forcemethod;
predictintercept = predictintercept;
forcescale = forcescale;
reversaldist = reversaldist;
peakdist = peakdist;
mindist = mindist;
maxdist = maxdist;
ambientspeed = ambientspeed;
speedscale = speedscale;""",
    'Pass Through',
]

_initialsnippets['popaxisforce/localshapeexpression'] = [
"""// 0: sphere
// 1: torus
type = type;
center = center;
axis = axis;
radius = radius;
height = height;""",
    'Pass Through',
]

_initialsnippets['popaxisforce/localspeedexpression'] = [
"""orbitspeed = orbitspeed;
liftspeed = liftspeed;
suctionspeed = suctionspeed;""",
    'Pass Through',
]

_initialsnippets['popaxisforce/localfalloffexpression'] = [
"""softedge = softedge;
innerstrength = innerstrength;
outerstrength = outerstrength;""",
    'Pass Through',
]

_initialsnippets['popaxisforce/localbehavior'] = [
"""treataswind = treataswind;
airresist = airresist;""",
    'Pass Through',
]

_initialsnippets['popcolor/localconstant'] = [
    "color = color;",
    'Pass Through',
    "color = @P;",
    'Position',
    "color = @Cd * 0.9;",
    'Darken Gradually',
]

_initialsnippets['popcolor/localrandom'] = [
    "seed += @ptnum;",
    'Random by Point',
    "seed += @id;",
    'Random by Id',
]

_initialsnippets['popcolor/localramp'] = [
    "ramp = @nage;",
    'Normalized Age',
    "ramp = @age;",
    'Age',
    "ramp = length(@v);",
    'Speed',
    "ramp = @P.y;",
    'Height',
]

_initialsnippets['popcolor/localblendramp'] = [
"""startcolor = startcolor;
endcolor = endcolor;
ramp = @nage;""",
    'Pass Through',
]

_initialsnippets['popcolor/localalphaconstant'] = [
    "alpha = alpha;",
    'Pass Through',
    "alpha = length(@v);",
    'Speed',
    "alpha = fit01(@nage, 1, 0);",
    'Fade with Age',
    'alpha = rand(@id + ch("../seed"));',
    'Random',
]

_initialsnippets['popcolor/localalpharamp'] = [
    "ramp = @nage;",
    'Pass Through',
]

_initialsnippets['popcurveforce/localradius'] = [
"""maxradius = maxradius;
airresist = airresist;""",
    'Pass Through',
]

_initialsnippets['popcurveforce/localforce'] = [
"""scalefollow = scalefollow;
scalesuction = scalesuction;
scaleorbit = scaleorbit;
scaleincomingvel = scaleincomingvel;""",
    'Pass Through',
]

_initialsnippets['popcurveincompressibleflow/localresist'] = [
"""airresist = airresist;
spinresist = spinresist;""",
    'Pass Through',
]

_initialsnippets['popcurveincompressibleflow/localvel'] = [
"""velscale = velscale;
velfallscale = velfallscale;""",
    'Pass Through',
]

_initialsnippets['popcurveincompressibleflow/localavel'] = [
"""avelscale = avelscale;
avelfallscale = avelfallscale;""",
    'Pass Through',
]

_initialsnippets['popdrag/localdragexpression'] = [
"""airresist = airresist;
windvelocity = windvelocity;""",
    'Pass Through',
"""airresist *= @nage;""",
    'Scale Drag by Normalized Age',
]

_initialsnippets['popdragspin/localdragexpression'] = [
"""spinresist = spinresist;
goalaxis = goalaxis;
goalspinspeed = goalspinspeed;""",
    'Pass Through',
"""spinresist *= @nage;""",
    'Scale Drag by Normalized Age',
]

_initialsnippets['popgroup/rulecode'] = [
    "ingroup = 1;",
    'All Particles',
    "ingroup = 0;",
    'No Particles',
    "ingroup = !(@id %5);",
    'Every Fifth Particle by Id',
    "ingroup = length(@v) > 1;",
    'Fast Particles',
]

_initialsnippets['popgroup/randomcode'] = [
"""seed = seed;
chance = chance;
randombehavior = randombehavior;""",
    'Pass Through',
]

_initialsnippets['popinstance/localexpression'] = [
"""instancepath = instancepath;
pscale = pscale;""",
    'Pass Through',
    'instancepath = sprintf("%s%d", instancepath, @id % 5);',
    "Every Fifth Id to Different Instance",
    'pscale *= fit01(@nage, 0.1, 1);',
    "Grow with Age",
]

_initialsnippets['popinteract/localforceexpression'] = [
"""positionforce = positionforce;
velforce = velforce;
coreradius = coreradius;
falloffradius = falloffradius;""",
    'Pass Through',
]

_initialsnippets['popkill/rulecode'] = [
    "dead = 1;",
    'All Particles',
    "dead = 0;",
    'No Particles',
    "dead = !(@id %5);",
    'Every Fifth Particle by Id',
    "dead = length(@v) > 1;",
    'Fast Particles',
    "dead = i@numhit > 0;",
    'Just Hit',
]

_initialsnippets['popkill/randomcode'] = [
"""seed = seed;
chance = chance;
randombehavior = randombehavior;""",
    'Pass Through',
]

_initialsnippets['poplocalforce/localforce'] = [
"""thrust = thrust;
lift = lift;
sideslip = sideslip;""",
    'Pass Through',
]

_initialsnippets['popproperty/localexpression'] = [
"""pscale = pscale;
mass = mass;
spinshape = spinshape;
bounce = bounce;
bounceforward = bounceforward;
friction = friction;
dynamicfriction = dynamicfriction;
drag = drag;
dragshape = dragshape;
dragcenter = dragcenter;
dragexp = dragexp;
cling = cling;""",
    'Pass Through',
]

_initialsnippets['poplookat/code'] = [
"""mode = mode;
method = method;
target = target;
refpath = refpath;
up = up;
dps = dps;
torque = torque;
spinresist = spinresist;
useup = useup;""",
    'Pass Through',
]

_initialsnippets['popsoftlimit/localexpression'] = [
"""t = t;
size = size;
// 0: Box, 1: Sphere
type = type;
invert = invert;
force = force;
vscale = vscale;""",
    'Pass Through',
]

_initialsnippets['popspeedlimit/localexpression'] = [
"""speedmin = speedmin;
speedmax = speedmax;
spinmin = spinmin;
spinmax = spinmax;""",
    'Pass Through',
]

_initialsnippets['popsprite/localexpression'] = [
"""spriteshop = spriteshop;

// 0: Uses offset/size
// 1: Uses textureindex/row/col
cropmode = cropmode;
textureoffset = textureoffset;
texturesize = texturesize;

textureindex = textureindex;
texturerow = texturerow;
texturecol = texturecol;

spriterot = spriterot;
spritescale = spritescale;""",
    'Pass Through',
]

_initialsnippets['poptorque/localforce'] = [
"""axis = axis;
amount = amount;""",
    'Pass Through',
]

_initialsnippets['popwind/localwindexpression'] = [
"""wind = wind;
windspeed = windspeed;
airresist = airresist;""",
    'Pass Through',
"""windspeed *= rand(@id);""",
    'Randomize Magnitude',
    "wind = length(wind) * cross(@P, {0, 1, 0}); ",
    'Orbit the Origin',
]

_initialsnippets['popwind/localnoiseexpression'] = [
"""amp = amp;
rough = rough;
atten = atten;
turb = turb;
pulselength = pulselength;
swirlscale = swirlscale;
swirlsize = swirlsize;
offset = offset;""",
    'Pass Through',
    "amp *= rand(@id);",
    'Randomize Amplitude',
]

_initialsnippets['popproximity/localexpression'] = [
"""distance = distance;
maxcount = maxcount;""",
    'Pass Through',
"""distance *= @pscale;""",
    'Scale by pscale',
]

_initialsnippets['popmetaballforce/localexpression'] = [
"""forcescale = forcescale;""",
    'Pass Through',
"""forcescale *= rand(@id);""",
    'Randomize by Id',
]

_initialsnippets['popadvectbyvolumes/localexpression'] = [
"""forcescale = forcescale;
velscale = velscale;
airresist = airresist;
velblend = velblend;
forceramp = forceramp;""",
    'Pass Through',
"""airresist *= rand(@id);
forcescale *= rand(@id);""",
    'Randomize by Id',
]

_initialsnippets['popspinbyvolumes/localexpression'] = [
"""torquescale = torquescale;
vorticityscale = vorticityscale;
spinresist = spinresist;
angvelblend = angvelblend;""",
    'Pass Through',
"""spinresist *= rand(@id);
torquescale *= rand(@id);""",
    'Randomize by Id',
]

_initialsnippets['popadvectbyvolumes/localexpression'] = [
"""forcescale = forcescale;
velscale = velscale;
airresist = airresist;
velblend = velblend;
forceramp = forceramp;""",
    'Pass Through',
"""airresist *= rand(@id);
forcescale *= rand(@id);""",
    'Randomize by Id',
]

_initialsnippets['rbdconstraintproperties/conelocalexpression'] = [
"""max_up_rotation = max_up_rotation;
max_out_rotation = max_out_rotation;
max_twist = max_twist;
softness = softness;
cfm = cfm;
bias_factor = bias_factor;
relaxation_factor = relaxation_factor;
positioncfm = positioncfm;
positionerp = positionerp;
goal_twist_axis = goal_twist_axis;
goal_up_axis = goal_up_axis;
constrained_twist_axis = constrained_twist_axis;
constrained_up_axis = constrained_up_axis;
disablecollisions = disablecollisions;
constraintiterations = constraintiterations;""",
    'Pass Through'
]

_initialsnippets['rbdconstraintproperties/gluelocalexpression'] = [
"""strength = strength;
halflife = halflife;
propagationrate = propagationrate;
propagationiterations = propagationiterations;""",
    'Pass Through',
"""float minS = 0.5;
float maxS = 1.5;
strength *= fit01(rand(@primnum), minS, maxS);""",
    'Randomize Strength'
]

_initialsnippets['rbdconstraintproperties/hardlocalexpression'] = [
"""cfm = cfm;
erp = erp;
numangularmotors = numangularmotors;
axis1 = axis1;
axis2 = axis2;
targetw = targetw;
maxangularimpulse = maxangularimpulse;
disablecollisions = disablecollisions;
constraintiterations = constraintiterations;""",
    'Pass Through'
]

_initialsnippets['rbdconstraintproperties/softlocalexpression'] = [
"""stiffness = stiffness;
dampingratio = dampingratio;
disablecollisions = disablecollisions;
constraintiterations = constraintiterations;""",
    'Pass Through',
"""float minS = 0.5;
float maxS = 1.5;
stiffness *= fit01(rand(@primnum), minS, maxS);""",
    'Randomize Stiffness'
]

# DOP version
_initialsnippets['vellumconstraintproperty/localexpression'] = [
"""stiffness = stiffness;
stiffnessexp = stiffnessexp;
compressstiffness = compressstiffness;
compressstiffnessexp = compressstiffnessexp;
dampingratio = dampingratio;
restlength = restlength;
restscale = restscale;
restvector = restvector;
plasticthreshold = plasticthreshold;
plasticrate = plasticrate;
plastichardening = plastichardening;
breakthreshold = breakthreshold;
breaktype = breaktype;
remove = remove;
broken = broken;""",
    'Pass Through',
]

# SOP version
_initialsnippets['vellumconstraintproperty/localexpression'] = [
"""stiffness = stiffness;
stiffnessexp = stiffnessexp;
compressstiffness = compressstiffness;
compressstiffnessexp = compressstiffnessexp;
dampingratio = dampingratio;
restlength = restlength;
restvector = restvector;
plasticthreshold = plasticthreshold;
plasticrate = plasticrate;
plastichardening = plastichardening;
breakthreshold = breakthreshold;
breaktype = breaktype;
remove = remove;""",
    'Pass Through',
]

# SOP version
_initialsnippets['rbdconetwistconstraintproperties/localexpression'] = [
"""max_up_rotation = max_up_rotation;
max_out_rotation = max_out_rotation;
max_twist = max_twist;
softness = softness;
computeinitialerror = computeinitialerror;
enablesoft = enablesoft;
angularlimitstiffness = angularlimitstiffness;
angularlimitdampingratio = angularlimitdampingratio;
twisttranslationrange = twisttranslationrange;
outtranslationrange = outtranslationrange;
uptranslationrange = uptranslationrange;
positionlimitstiffness = positionlimitstiffness;
positionlimitdampingratio = positionlimitdampingratio;
cfm = cfm;
bias_factor = bias_factor;
relaxation_factor = relaxation_factor;
positioncfm = positioncfm;
positionerp = positionerp;
goal_twist_axis = goal_twist_axis;
goal_up_axis = goal_up_axis;
constrained_twist_axis = constrained_twist_axis;
constrained_up_axis = constrained_up_axis;
motor_enabled = motor_enabled;
motor_targetcurrentpose = motor_targetcurrentpose;
motor_target = motor_target;
motor_targetp = motor_targetp;
motor_hastargetprev = motor_hastargetprev;
motor_targetprev = motor_targetprev;
motor_targetprevp = motor_targetprevp;
motor_normalizemaximpulse = motor_normalizemaximpulse;
motor_maximpulse = motor_maximpulse;
motor_erp = motor_erp;
motor_cfm = motor_cfm;
motor_targetangularstiffness = motor_targetangularstiffness;
motor_targetangulardampingratio = motor_targetangulardampingratio;
motor_targetpositionstiffness = motor_targetpositionstiffness;
motor_targetpositiondampingratio = motor_targetpositiondampingratio;
disablecollisions = disablecollisions;
numiterations = numiterations;
restlength = restlength;
Cd = Cd;""",
    'Pass Through',
]

# LOP version
_initialsnippets['lpetag/vexpression'] = [
"""tag = tag;""",
    'Pass Through',
]


def installInitialSnippets():
    """ Copies the initial snippets into _vexsnippets and adds
        the comment prefix.
    """
    for parm in _initialsnippets:
        rawlist = _initialsnippets[parm]
        pairlist = list(zip(rawlist[::2], rawlist[1::2]))
        item_list = []
        sol_list = []
        for (body, title) in pairlist:
            sol_list.append(body.strip())
            sol_list.append(title)
            body = '// ' + title + '\n' + body
            item_list.append(body)
            item_list.append(title)
        _vexsnippets[parm] = item_list
        _vexsnippets_sol[parm] = sol_list


def ensureSnippetsAreLoaded():
    global _hasloadedsnippets

    if not _hasloadedsnippets:
        _hasloadedsnippets = True
        installInitialSnippets()
        (snippets, snippets_sol) = snippetmenu.loadSnippets(
            hou.findFiles('VEXpressions.txt'), '//')
        _vexsnippets.update(snippets)
        _vexsnippets_sol.update(snippets_sol)


def buildSnippetMenu(snippetname, multiparm_indices=[], kwargs: dict = {}):
    """ Given a snippetname, determine what
        snippets should be generated.
        Optionally provide the kwargs dict to extend the list with available recipes.
    """
    ensureSnippetsAreLoaded()
    snippetlist = []
    if snippetname in _vexsnippets:
        snippetlist.extend(snippetmenu.expandMultiparms(
            list(_vexsnippets[snippetname]),
            multiparm_indices))

    if kwargs:
        from recipeutils import buildSnippetMenuFromRecipes
        snippetlist.extend(buildSnippetMenuFromRecipes(kwargs))

    if snippetlist:
        return snippetlist

    return ["", "None"]


def buildSingleLineSnippetMenu(snippetname, multiparm_indices=[], kwargs: dict = {}):
    """ Given a snippetname, determine what
        snippets should be generated.
        Optionally provide the kwargs dict to extend the list with available recipes.
    """
    ensureSnippetsAreLoaded()
    snippetlist = []
    if snippetname in _vexsnippets_sol:
        snippetlist.extend(snippetmenu.expandMultiparms(
            list(_vexsnippets_sol[snippetname]),
            multiparm_indices))

    if kwargs:
        from recipeutils import buildSnippetMenuFromRecipes
        snippetlist.extend(buildSnippetMenuFromRecipes(kwargs))

    if snippetlist:
        return snippetlist

    return ["", "None"]


# Strings representing channel calls
chcalls = [
    'ch', 'chf', 'chi', 'chu', 'chv', 'chp', 'ch2', 'ch3', 'ch4',
    'vector(chramp', 'chramp',
    'vector(chrampderiv', 'chrampderiv',
    'chs',
    'chdict', 'chsop'
]
# Expression for finding ch calls
chcall_exp = re.compile(f"""
\\b  # Start at word boundary
({"|".join(re.escape(chcall) for chcall in chcalls)})  # Match any call string
\\s*[(]\\s*  # Opening bracket, ignore any surrounding whitespace
('\\w+'|"\\w+")  # Single or double quoted string
\\s*[),]  # Optional white space and closing bracket or comma marking end of first argument
""", re.VERBOSE)
# Number of components corresponding to different ch calls. If a call string is
# not in this dict, it's assumed to have a single component.
ch_size = {
    'chu': 2, 'chv': 3, 'chp': 4, 'ch2': 4, 'ch3': 9, 'ch4': 16,
}
# This expression matches comments (single and multiline) and also strings
# (though it will miss strings with escaped quote characters).
comment_or_string_exp = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE
)


# This subsitution function replaces comments with spaces and leaves strings
# alone. This has the effect of skipping over strings so it doesn't get confused
# by comment characters inside a string.
def remove_comments(match):
    s = match.group(0)
    if s.startswith('/'):
        return ' '
    else:
        return s

def _addSpareParmsToStandardFolder(node, parmname, refs):
    """
    Takes a list of (name, template) in refs and injects them into the
    standard-named folder for generated parms.  If it doesn't exist,
    create the folder and place before parmname.
    """
    if not refs:
        return          # No-op

    # We consider a multiparm any parameter with a number in it.
    # This might have false positives, but it is important to not try
    # to create a parameter before a multiparm as that slot
    # won't exist.  We also use a single standard folder name
    # for all the multiparm snippets.
    ismultiparm = any(map(str.isdigit, parmname))

    ptg = node.parmTemplateGroup()
    foldername = 'folder_generatedparms_' + parmname
    if ismultiparm:
        foldername = 'folder_generatedparms'

    folder = ptg.find(foldername)
    if not folder:
        folder = hou.FolderParmTemplate(
            foldername,
            "Generated Channel Parameters",
            folder_type=hou.folderType.Simple,
        )
        folder.setTags({"sidefx::look": "blank"})
        if not ismultiparm:
            ptg.insertBefore(parmname, folder)
        else:
            ptg.insertBefore(ptg.entries()[0], folder)

    # Insert/replace the parameter templates
    indices = ptg.findIndices(folder)
    for name, template in refs:
        exparm = node.parm(name) or node.parmTuple(name)
        if exparm:
            ptg.replace(name, template)
        else:
            ptg.appendToFolder(indices, template)
    node.setParmTemplateGroup(ptg)

def createSpareParmsFromOCLBindings(node, parmname):
    """ 
    Parse the @BIND commands in an OpenCL kernel and create corresponding
    spare parameters
    """
    parm = node.parm(parmname)
    code = parm.evalAsString()

    # Extract bindings
    bindings = hou.text.oclExtractBindings(code)
    runover = hou.text.oclExtractRunOver(code)

    channellinks = []
    ramplinks = []
    refs = []

    ispython = False
    if parm.parmTemplate().tags().get('editorlang', '') == 'python':
        ispython = True
    iscop = False
    if node.type().category() == hou.copNodeTypeCategory():
        iscop = True
    hasoutputlayer = False

    # apply the runover.
    if runover != '' and not ispython:
        r = node.parm('runover')
        if r is None:
            r = node.parm('options_runover')
        if r is not None:
            try:
                r.set(runover)
            except hou.OperationFailed:
                try:
                    if runover == 'field':
                        r.set('allfields')
                    if runover == 'attribute':
                        r.set('firstattribute')
                except hou.OperationFailed:
                    # likely an unsupported run over.
                    pass

    # Sadly, SOP and DOP opencl have completely different
    # binding names.  Use the base bindings type to differentiate
    if node.parm('bindings') is not None:
        # SOP based (also COP)
        bindparm = 'bindings'
        bindparmprefix = 'bindings'
        bindparmsuffix = {
            'name' : '_name',
            'type'   : '_type',
            'ramp' : '_ramp',
            'ramptype' : '_ramptype',
            'rampsize' : '_rampsize',
            'layertype' : '_layertype',
            'layerborder' : '_layerborder',
            'volume' : '_volume',
            'geometry' : '_geometry',
            'input' : '_input',
            'portname' : '_portname',
            'vdbtype' : '_vdbtype',
            'forcealign' : '_forcealign',
            'resolution' : '_resolution',
            'voxelsize' : '_voxelsize',
            'xformtoworld' : '_xformtoworld',
            'xformtovoxel' : '_xformtovoxel',
            'attribute' : '_attribute',
            'attribclass' : '_attribclass',
            'attribtype' : '_attribtype',
            'attribsize' : '_attribsize',
            'precision' : '_precision',
            'readable' : '_readable',
            'writeable' : '_writeable',
            'optional' : '_optional',
            'defval' : '_defval',
            'timescale' : '_timescale',
            'sval' : '_sval',
            'intval' : '_intval',
            'fval'   : '_fval',
            'v2val'  : '_v2val',
            'v3val'  : '_v3val',
            'v4val'  : '_v4val',
            }
    elif node.parm('paramcount') is not None:
        # DOP based
        bindparm = 'paramcount'
        bindparmprefix = 'parameter'
        bindparmsuffix = {
            'name' : 'Name',
            'type'   : 'Type',
            'ramp' : 'Ramp',
            'rampsize' : 'RampSize',
            'volume' : 'Volume',
            'geometry' : 'Geometry',
            'input' : None,
            'portname' : None,
            'vdbtype' : None,
            'forcealign' : None,
            'resolution' : 'Resolution',
            'voxelsize' : 'VoxelSize',
            'xformtoworld' : 'XformToWorld',
            'xformtovoxel' : 'XformToVoxel',
            'attribute' : 'Attribute',
            'attribclass' : 'Class',
            'attribtype' : 'AttributeType',
            'attribsize' : 'AttributeSize',
            'precision' : 'Precision',
            'readable' : 'Input',
            'writeable' : 'Output',
            'optional' : 'Optional',
            'defval' : 'DefVal',
            'timescale' : 'TimeScale',
            'intval' : 'Int',
            'fval'   : 'Flt',
            'v2val'  : 'Flt2',
            'v3val'  : 'Flt3',
            'v4val'  : 'Flt4',
        }
    else:
        # Unknown
        pass

    inputs = node.parm('inputs')
    outputs = node.parm('outputs')

    # Loop over each binding to see if it exists on explicit bindings,
    # if not add it.
    for binding in bindings:
        isgeo = binding['type'] in ('attribute', 'volume', 'vdb', 'geo')
        isgeodata = binding['type'] in ('attribute', 'volume', 'vdb')
        isvdb = binding['type'] in ('vdb', )
        islayer = binding['type'] == 'layer'

        # Search our node's bindings...
        numbind = node.parm(bindparm).evalAsInt()
        found = False
        for i in range(1, numbind+1):
            name = node.parm(bindparmprefix + str(i) + bindparmsuffix['name']).evalAsString()
            if name == binding['name']:
                found = True
                break
        if not found:
            requiresparm = False
            tuplesize = 1
            isint = False
            isstring = False
            isramp = False

            # Add to our list if we should have spare parms...
            if binding['type'] in ('string', 'int', 'float', 'float2', 'float3', 'float4'):
                requiresparm = True
                if binding['type'] == 'int':
                    isint = True
                if binding['type'] == 'float2':
                    tuplesize = 2
                    # Only cops supports v2
                    if not iscop:
                        requiresparm = False
                if binding['type'] == 'float3':
                    tuplesize = 3
                if binding['type'] == 'float4':
                    tuplesize = 4
                if binding['type'] == 'string':
                    isstring = True
                    if not ispython:
                        requiresparm = False

            # If it is optional and has a defval we want to
            # trigger it
            if isgeodata and binding['readable'] and binding['optional'] and binding['defval']:
                requiresparm = True
                # Some cases we don't support...
                if binding['type'] == 'attribute':
                    if binding['attribtype'] == 'floatarray' or binding['attribtype'] == 'intarray':
                        requiresparm = False
                    elif binding['attribtype'] == 'int':
                        isint = True
                        if binding['attribsize'] != 1:
                            requiresparm = False
                    elif binding['attribtype'] == 'float':
                        tuplesize = binding['attribsize']
                        if tuplesize not in (1, 3, 4):
                            requiresparm = False
                # Python doesn't support optional
                if ispython:
                    requiresparm = False

            # extraparm does not work for layer, and may not be wanted
            # if islayer and binding['readable'] and binding['optional'] and binding['defval']:
            #    requiresparm = True

            if binding['type'] == 'ramp':
                isramp = True
                requiresparm = True
                ramptype = hou.rampParmType.Color
                if binding['ramptype'] == 'float':
                    ramptype = hou.rampParmType.Float

            name = binding['name']
            label = name.title().replace("_", " ")
            if requiresparm:
                # We want to avoid conflict with existing OpenCL parms.
                # we have no need to exactly match as the source isn't a
                # ch("") like it is in VEX.
                internalname = name + '_val'

                # In cops we have prefixed internal parms so we don't
                # have to worry about conflicts so much, but we want to
                # fall back to _val if that already existed.
                # This is also true for python snippets.
                exparm = node.parm(internalname) or node.parmTuple(internalname)
                if not exparm and (iscop or ispython):
                    internalname = name

                if isramp:
                    template = hou.RampParmTemplate(internalname, label, ramptype)
                elif isint:
                    template = hou.IntParmTemplate(internalname, label, tuplesize)
                elif isstring:
                    template = hou.StringParmTemplate(internalname, label, tuplesize)
                else:
                    template = hou.FloatParmTemplate(internalname, label, tuplesize, min=0, max=1)

                # Check if we have an existing parm.
                # note the user may have removed an explicit binding,
                # but left the existing parm, in this case we'll link
                # to that...
                exparm = node.parm(internalname) or node.parmTuple(internalname)
                if not exparm:
                    refs.append((internalname, template))

                # Create our new binding...
                node.parm(bindparm).set(numbind+1)
                numbind += 1

                # Write back our binding values...
                for key in bindparmsuffix:
                    if bindparmsuffix[key] is None:
                        continue
                    if key in ('sval', 'intval', 'fval', 'v2val', 'v3val', 'v4val', 'v4bval', 'm4val', 'ramp'):
                        continue
                    keyparmname = bindparmprefix + str(numbind) + bindparmsuffix[key]
                    parm = node.parm(keyparmname) or node.parmTuple(keyparmname)
                    if parm: parm.set(binding[key])
                if isramp:
                    s = '_ramp_rgb' if ramptype == hou.rampParmType.Color else bindparmsuffix['ramp']
                    ramplinks.append(( internalname, bindparmprefix + str(numbind) + s))
                else:
                    if isint:
                        t = 'intval'
                    elif isstring:
                        t = 'sval'
                    elif tuplesize == 1:
                        t = 'fval'
                    else:
                        t = 'v%dval' % tuplesize
                    channellinks.append(( internalname,  bindparmprefix + str(numbind) + bindparmsuffix[t], binding[t]))

        if inputs is not None and (binding['readable'] or (not binding['readable'] and not binding['writeable'])) and (isgeo or islayer):
            num = inputs.evalAsInt()
            found = False
            lookupname = binding['portname']
            if lookupname == '':
                lookupname = binding['name']
            for i in range(1, num+1):
                name = node.parm('input' + str(i) + '_name').evalAsString()
                if name == lookupname:
                    found = True
                    break
            if not found:
                inputs.set(num+1)
                i = num+1
                node.parm('input' + str(i) + '_name').set(lookupname)
                if isgeo:
                    layertype = 'geo'
                    # If the binding name matches port name, we assume
                    # a pure VDB...  We need to know the type though.
                    if isvdb and lookupname == binding['name']:
                        vdbtype = binding['vdbtype']
                        if vdbtype == 'float':
                            layertype = 'fvdb'
                        elif vdbtype == 'vector':
                            layertype = 'vvdb'
                        elif vdbtype == 'int':
                            layertype = 'ivdb'
                        elif vdbtype == 'floatn':
                            layertype = 'fnvdb'
                        # Default is to stay 'geo' for an any binding.
                else:
                    if not binding['readable'] and not binding['writeable']:
                        layertype = 'metadata'
                    else:
                        layertype = binding['layertype']
                if layertype == 'float?': layertype = 'floatn'
                node.parm('input' + str(i) + '_type').set(layertype)
                node.parm('input' + str(i) + '_optional').set(binding['optional'])

        if outputs is not None and binding['writeable'] and (isgeo or islayer):
            num = outputs.evalAsInt()
            found = False
            lookupname = binding['portname']
            hasoutputlayer = hasoutputlayer or islayer
            if lookupname == '':
                lookupname = binding['name']
            for i in range(1, num+1):
                name = node.parm('output' + str(i) + '_name').evalAsString()
                if name == lookupname:
                    found = True
                    break
            if not found:
                outputs.set(num+1)
                i = num+1
                node.parm('output' + str(i) + '_name').set(lookupname)
                if isgeo:
                    layertype = 'geo'
                    # If the binding name matches port name, we assume
                    # a pure VDB...  We need to know the type though.
                    if isvdb and lookupname == binding['name']:
                        vdbtype = binding['vdbtype']
                        if vdbtype == 'float':
                            layertype = 'fvdb'
                        elif vdbtype == 'vector':
                            layertype = 'vvdb'
                        elif vdbtype == 'int':
                            layertype = 'ivdb'
                        elif vdbtype == 'floatn':
                            layertype = 'fnvdb'
                        # Default is to stay 'geo' for an any binding.
                else:
                    layertype = binding['layertype']
                    if layertype == 'float?': layertype = 'floatn'
                node.parm('output' + str(i) + '_type').set(layertype)
                if isvdb and binding['readable']:
                    # Take corresponding named input as our meta source
                    node.parm('output' + str(i) + '_metadata').set('match')

    # Add an unbound input to provide output layer size
    # This is only necessary if we have a layer output.
    if inputs is not None and outputs is not None and not inputs.evalAsInt() and outputs.evalAsInt() and hasoutputlayer:
        inputs.set(1)
        node.parm('input1_name').set('')
        node.parm('input1_optional').set(True)

    # Completed the binding loop, we've extended our bindings to have
    # all the new explicit bindings that we think need parms and build
    # a refs list of them.  channellinks has triples of how we want
    # to then re-link, which we can do after the refs are built.
    _addSpareParmsToStandardFolder(node, parmname, refs)

    for (internalname, srcname, value) in channellinks:
        parm = node.parm(internalname) or node.parmTuple(internalname)
        if parm:
            parm.set(value)
            srcparm = node.parm(srcname) or node.parmTuple(srcname)
            if srcparm: srcparm.set(parm)

    for (internalname, srcname) in ramplinks:
        parm = node.parm(internalname) or node.parmTuple(internalname)
        lin = hou.rampBasis.Linear
        if parm: parm.set(hou.Ramp((lin, lin),(0,1),(0,1)))
        srcparm = node.parm(srcname) or node.parmTuple(srcname)

        if srcparm:
            # Destory all channels in the source parm as multiparm will
            # clone them.
            npt = srcparm.evalAsInt()
            for i in range(npt):
                node.parm(srcname + str(i+1) + 'pos').deleteAllKeyframes()
                node.parm(srcname + str(i+1) + 'interp').deleteAllKeyframes()
                x = node.parm(internalname + str(i+1) + 'value')
                if x:
                    node.parm(srcname + str(i+1) + 'value').deleteAllKeyframes()
                else:
                    node.parm(srcname + str(i+1) + 'cr').deleteAllKeyframes()
                    node.parm(srcname + str(i+1) + 'cg').deleteAllKeyframes()
                    node.parm(srcname + str(i+1) + 'cb').deleteAllKeyframes()

        # Link the point count
        if srcparm: srcparm.setExpression("ch('" + internalname + "')")

        # Setup opmultiparms
        cmd = 'opmultiparm ' + node.path() + ' "' + srcname + '#pos" "' + internalname + '#pos" "' + srcname + '#value" "' + internalname + '#value" "' + srcname + '#interp" "' + internalname + '#interp" "' + srcname + '#cr" "' + internalname + '#cr" "' + srcname + '#cg" "' + internalname + '#cg" "' + srcname + '#cb" "' + internalname + '#cb"'
        (res, err) = hou.hscript(cmd)

        # Manually link already exisiting parms
        # this should be evalAsInt, but for some reason that is still
        # 1 at this point?
        npt = 2 # parm.evalAsInt()
        for i in range(npt):
            node.parm(srcname + str(i+1) + 'pos').set(node.parm(internalname + str(i+1) + 'pos'))
            node.parm(srcname + str(i+1) + 'interp').set(node.parm(internalname + str(i+1) + 'interp'))
            x = node.parm(internalname + str(i+1) + 'value')
            if x:
                node.parm(srcname + str(i+1) + 'value').set(x)
            else:
                node.parm(srcname + str(i+1) + 'cr').set(node.parm(internalname + str(i+1) + 'cr'))
                node.parm(srcname + str(i+1) + 'cg').set(node.parm(internalname + str(i+1) + 'cg'))
                node.parm(srcname + str(i+1) + 'cb').set(node.parm(internalname + str(i+1) + 'cb'))

    # no need to dirty an opencl node as we affected cooking parmeters
    # when we updated bindings.

def createSpareParmsFromChCalls(node, parmname):
    """
    For each ch() call in the given parm name, create a corresponding spare
    parameter on the node.
    """

    parm = node.parm(parmname)
    original = parm.unexpandedString()
    simple = True
    if len(parm.keyframes()) > 0:
        # The parm has an expression/keyframes, evaluate it to the get its
        # current value
        code = parm.evalAsString()
        simple = False
    else:
        code = original.strip()
        if len(code) > 2 and code.startswith("`") and code.endswith("`"):
            # The whole string is in backticks, evaluate it
            code = parm.evalAsString()
            simple = False
    # Remove comments
    code = comment_or_string_exp.sub(remove_comments, code)

    # Loop over the channel refs found in the VEX, work out the corresponding
    # template type, remember for later (we might need to check first if the
    # user wants to replace existing parms).
    refs = []
    existing = []
    foundnames = set()
    for match in chcall_exp.finditer(code):
        call = match.group(1)
        name = match.group(2)[1:-1]

        # If the same parm shows up more than once, only track the first
        # case.  This avoids us double-adding since we delay actual
        # creation of parms until we've run over everything.
        if name in foundnames:
            continue
        foundnames.add(name)
        
        size = ch_size.get(call, 1)
        label = name.title().replace("_", " ")

        if call in ("vector(chramp", "vector(chrampderiv"):
            # Result was cast to a vector, assume it's a color
            template = hou.RampParmTemplate(name, label, hou.rampParmType.Color)
        elif call in ("chramp", "chrampderiv"):
            # No explicit cast, assume it's a float
            template = hou.RampParmTemplate(name, label, hou.rampParmType.Float)
        elif call == "chs":
            template = hou.StringParmTemplate(name, label, size)
        elif call == "chsop":
            template = hou.StringParmTemplate(
                name, label, size, string_type=hou.stringParmType.NodeReference)
        elif call == "chi":
            template = hou.IntParmTemplate(name, label, size)
        elif call == "chdict":
            template = hou.DataParmTemplate(
                name, label, size,
                data_parm_type=hou.dataParmType.KeyValueDictionary
            )
        else:
            template = hou.FloatParmTemplate(name, label, size, min=0, max=1)

        exparm = node.parm(name) or node.parmTuple(name)
        if exparm:
            if not exparm.isSpare():
                # The existing parameter isn't a spare, so just skip it
                continue
            extemplate = exparm.parmTemplate()
            etype = extemplate.type()
            ttype = template.type()
            if (
                etype != ttype or
                extemplate.numComponents() != template.numComponents() or
                (ttype == hou.parmTemplateType.String and
                 extemplate.stringType() != template.stringType())
            ):
                # The template type is different, remember the name and template
                # type to replace later
                existing.append((name, template))
            else:
                # No difference in template type, we can skip this
                continue
        else:
            # Remember the parameter name and template type to insert later
            refs.append((name, template))

    # If there are existing parms with the same names but different template
    # types, ask the user if they want to replace them
    if existing:
        exnames = ", ".join(f'"{name}"' for name, _ in existing)
        if len(existing) > 1:
            msg = f"Parameters {exnames} already exist, replace them?"
        else:
            msg = f"Parameter {exnames} already exists, replace it?"
        result = hou.ui.displayCustomConfirmation(
            msg, ("Replace", "Skip Existing", "Cancel"), close_choice=2,
            title="Replace Existing Parameters?",
            suppress=hou.confirmType.DeleteSpareParameters,
        )
        if result == 0:  # Replace
            refs.extend(existing)
        elif result == 2:  # Cancel
            return

    _addSpareParmsToStandardFolder(node, parmname, refs)

    if refs:
        if simple:
            # Re-write the contents of the snippet so the node will re-run the
            # VEX and discover the new parameters.
            # (This is really a workaround for a bug (#123616), since Houdini
            # should ideally know to update VEX snippets automatically).
            parm.set(original)


