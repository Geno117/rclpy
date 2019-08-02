# Copyright 2018 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading


class Context:
    """
    Encapsulates the lifecycle of init and shutdown.

    Context objects should not be reused, and are finalized in their destructor.

    Wraps the `rcl_context_t` type.
    """

    def __init__(self):
        from rclpy.impl.implementation_singleton import rclpy_implementation
        self._handle = rclpy_implementation.rclpy_create_context()
        self._lock = threading.Lock()
        self._guard_lock = threading.RLock()
        self._guard_conditions = {}

    @property
    def handle(self):
        return self._handle

    def get_interrupt_guard_condition(self, wait_set):
        with self._guard_lock:
            from .guard_condition import GuardCondition
            if wait_set not in self._guard_conditions:
                self._guard_conditions[wait_set] = GuardCondition(
                    callback=None, callback_group=None, context=self)
            return self._guard_conditions[wait_set]

    def release_interrupt_guard_condition(self, wait_set):
        with self._guard_lock:
            if wait_set in self._guard_conditions:
                self._guard_conditions[wait_set].destroy()
                del self._guard_conditions[wait_set]

    def interrupt_wait_sets(self):
        with self._guard_lock:
            for gc in self._guard_conditions.values():
                gc.trigger()

    def ok(self):
        # imported locally to avoid loading extensions on module import
        from rclpy.impl.implementation_singleton import rclpy_implementation
        with self._lock:
            return rclpy_implementation.rclpy_ok(self._handle)

    def shutdown(self):
        # imported locally to avoid loading extensions on module import
        from rclpy.impl.implementation_singleton import rclpy_implementation
        with self._lock:
            rclpy_implementation.rclpy_shutdown(self._handle)
            self.interrupt_wait_sets()

    def try_shutdown(self):
        """Shutdown rclpy if not already shutdown."""
        # imported locally to avoid loading extensions on module import
        from rclpy.impl.implementation_singleton import rclpy_implementation
        with self._lock:
            if rclpy_implementation.rclpy_ok(self._handle):
                return rclpy_implementation.rclpy_shutdown(self._handle)
