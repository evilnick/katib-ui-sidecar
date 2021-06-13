#!/usr/bin/env python3
# Copyright 2021 evilnick
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus
from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

logger = logging.getLogger(__name__)


class KatibUiSidecarCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.katib_ui_pebble_ready, self._on_katib_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        # self.framework.observe(self.on.ingress_relation_changed, self.ingress_relation)
        self.ingress = IngressRequires(
                        self, {"service-hostname": "katib-ui",
                        "service-name": self.model.app.name,
                        "service-port": self.config["port"]})
        self._stored.set_default(store={})

    def _on_katib_ui_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        TEMPLATE-TODO: change this example to suit your needs.
        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """
        # Get a reference to the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "katib-ui layer",
            "description": "pebble config layer for katib-ui",
            "services": {
                "katib-ui": {
                    "override": "replace",
                    "summary": "katib-ui",
                    "command": "./katib-ui",
                    "startup": "enabled",
                    "environment": {"KATIB_PORT": self.model.config["port"]},
                }
            }
        }
        # Add intial Pebble config layer using the Pebble API
        container.add_layer("katib-ui", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, _):
        # Update port for katib from config 
        logger.debug("port reconfigured to : %r", self.config["port"])
        # N.B. currently, there is only a single config value. As this
        # event is not triggered unless the value *changes* (i.e. 
        # running juju config and setting the port to the same value
        # will not trigger this event), there is no need to check if 
        # the port has changed - it definitely has.
        self.unit.status = MaintenanceStatus("Configuring")
        # katib needs to be re-run with a new port
        logger.info("Finished config_changed")
        self.unit.status = ActiveStatus()

if __name__ == "__main__":
    main(KatibUiSidecarCharm)
