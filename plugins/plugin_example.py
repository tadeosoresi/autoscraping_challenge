class AirflowPlugin:
    # The name of your plugin (str)
    name = None
    # A list of class(es) derived from BaseHook
    hooks = []
    # A list of references to inject into the macros namespace
    macros = []
    # A list of Blueprint object created from flask.Blueprint. For use with the flask_appbuilder based GUI
    flask_blueprints = []
    # A list of dictionaries containing FlaskAppBuilder BaseView object and some metadata. See example below
    appbuilder_views = []
    # A list of dictionaries containing kwargs for FlaskAppBuilder add_link. See example below
    appbuilder_menu_items = []

    # A callback to perform actions when airflow starts and the plugin is loaded.
    # NOTE: Ensure your plugin has *args, and **kwargs in the method definition
    #   to protect against extra parameters injected into the on_load(...)
    #   function in future changes
    def on_load(*args, **kwargs):
        # ... perform Plugin boot actions
        pass

    # A list of global operator extra links that can redirect users to
    # external systems. These extra links will be available on the
    # task page in the form of buttons.
    #
    # Note: the global operator extra link can be overridden at each
    # operator level.
    global_operator_extra_links = []

    # A list of operator extra links to override or add operator links
    # to existing Airflow Operators.
    # These extra links will be available on the task page in form of
    # buttons.
    operator_extra_links = []

    # A list of timetable classes to register so they can be used in DAGs.
    timetables = []

    # A list of Listeners that plugin provides. Listeners can register to
    # listen to particular events that happen in Airflow, like
    # TaskInstance state changes. Listeners are python modules.
    listeners = []